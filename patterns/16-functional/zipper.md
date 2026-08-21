---
name: Zipper
slug: zipper
family: 16-functional
category: Data and State
aliases: [Huet Zipper, One-Hole Context, Tree Zipper, Location]
first_described: "Huet 1997"
maturity: canonical
related: [persistent-data-structures, structural-sharing, lens, immutability, iterator]
incompatible_with: [shared-mutable-tree, in-place-tree-mutation]
verified: 2026-08-21
---

# Zipper

## 1. Name, aliases, and lineage

The canonical name is Zipper. Gerard Huet introduced it in a two-page
functional pearl, "The Zipper", published in the Journal of Functional
Programming, volume 7, issue 5, pages 549 to 554, September 1997
(https://www.st.cs.uni-saarland.de/edu/seminare/2005/advanced-fp/docs/huet-zipper.pdf,
verified 2026-08-21). Huet states the problem plainly at the top of the
paper. represent a tree together with a subtree that is the focus of
attention, where that focus may move left, right, up, or down, and where
moving the focus and editing at the focus are both cheap. He names the data
structure a zipper because moving the focus is like running a zip fastener
up and down a seam, closing the path behind the old focus and opening it
in front of the new one.

Huet's own paper uses the term **location** for a pair of a subtree and its
surrounding context, which some Lisp and Scheme implementations still use
as the name of the paired value. **Huet Zipper** distinguishes the
original tree-shaped construction from later generalisations. **One-Hole
Context** is the type-theoretic name for the context half of the pair, used
in the generalisation this entry covers in dimension 8. **Tree Zipper**
disambiguates from list-specific or string-specific zippers, which are
degenerate cases of the same idea on a simpler shape.

The Wikipedia summary of the construction, used here only to confirm
common phrasing and not as an explanatory source, describes a zipper as a
technique of representing an aggregate data structure so that it is
convenient for writing programs that traverse the structure arbitrarily
and update its contents, especially in purely functional programming
languages (https://en.wikipedia.org/wiki/Zipper_(data_structure), verified
2026-08-21).

A separate and later strand of the lineage matters for dimension 8. Conor
McBride, "The Derivative of a Regular Type is its Type of One-Hole
Contexts", 2001 (http://strictlypositive.org/diff.pdf, verified
2026-08-21), proved that the type of one-hole contexts for a regular data
type is exactly the formal derivative of that type, in the sense of
Leibniz calculus applied to the algebra of sum and product types. McBride's
result explains why a zipper can be derived mechanically for any
recursively defined type built from the usual combinators, rather than
invented by hand for each shape, and it is the reason this pattern
generalises past trees.

## 2. Problem and context

A program holds an immutable, recursively defined structure, most often a
tree but sometimes a list, and it needs to walk to an arbitrary position
inside that structure, read or change the value there, and continue
walking, all without copying the whole structure on every step and without
mutating any node in place.

The situation reads like this in a codebase. A syntax tree is parsed once
and then an editor, a linter, or a refactoring tool needs to move a cursor
around inside it, insert a node, replace a node, or delete a node, then
move again. A rose-tree file system model needs to focus on one directory,
list its siblings, move up to the parent, then move down into a different
child. A window manager keeps a tree or a list of workspaces and needs to
shift focus left and right cheaply on every keypress. In every case the
naive approach either mutates the structure in place, which breaks the
immutability the rest of the program relies on and makes undo and sharing
hard, or it rebuilds the whole structure from the root on every move,
which is correct but throws away the locality of the edit and costs time
proportional to the size of the whole structure rather than the depth of
the cursor.

The context that makes a zipper the right answer has three parts.

- The structure is recursively defined and immutable, so an edit must
  produce a new value rather than mutate the old one.
- The program performs a sequence of nearby moves and edits, not one
  isolated lookup, so the cost of setting up the cursor should be paid
  once and amortised across the sequence.
- The structure is walked by a human or by an algorithm that reasons
  locally, one step at a time, rather than by a query language that can
  jump directly to an arbitrary node by index or by path.

Outside that context the pattern is unnecessary machinery, see dimension
4.

## 3. Forces

The pattern balances the following competing pressures.

- **Locality of edit cost.** Favoured. An edit at the focus, and a single
  step of movement, cost time proportional to the depth of the cursor from
  the root, never the size of the whole structure. This is the entire
  reason the pattern exists.
- **Immutability.** Favoured. Every zipper operation returns a new zipper
  value. The original tree and every earlier zipper value the program
  still holds remain valid and unchanged, which is judgement grounded in
  how the persistent-data-structures family generally trades allocation
  for safe sharing.
- **Sharing.** Favoured, by construction rather than by a separate
  mechanism. The part of the tree not on the path from the root to the
  focus is untouched and is shared by reference between the old tree and
  the new one produced after an edit, exactly the mechanism the
  structural-sharing entry in this family describes in general.
- **Memory overhead per step.** Sacrificed. Each step of movement away
  from the root allocates one context frame recording the siblings passed
  and the direction taken, so a zipper focused deep in a wide tree holds
  more live data than a bare pointer into a mutable tree would.
- **API surface.** Sacrificed. A zipper needs a family of navigation
  functions, up, down, left, right, plus edit and rebuild operations,
  where a mutable in-place tree needs none of this, only field
  assignment.
- **Type complexity in a statically typed language.** Sacrificed, and
  more so for a heterogeneous tree such as a syntax tree with many node
  shapes, where each shape's one-hole context is itself a distinct type,
  see dimension 8.
- **Random access by index or key.** Not addressed, and actively worse
  than a direct indexed structure. A zipper is built for a walk that
  visits neighbouring positions, not for jumping to an arbitrary position
  by key in one step.
- **Reasoning simplicity.** Favoured for the caller. Once a zipper is
  built, up, down, left, and right all read as plain function calls with
  no exceptions for edge cases beyond an explicit "cannot move" result, so
  the traversal code itself stays free of index arithmetic.

## 4. Applicability and non-applicability

Reach for a Zipper when the following hold.

- The structure is immutable and recursively defined, a tree, a rose
  tree, or a list, and the program needs to focus on one position and
  move relative to it repeatedly.
- Edits happen near each other in a sequence, a cursor moving through an
  editor buffer, a linter walking and rewriting an abstract syntax tree,
  a game board cursor stepping between cells.
- The caller wants undo, redo, or branching exploration, because each
  zipper value along the way is a distinct, cheap, still-valid immutable
  snapshot that earlier steps can be resumed from.
- The program is written in, or interoperates cleanly with, a language
  where persistent data structures and algebraic data types are the
  normal way to model a tree, so the context type can be derived
  naturally from the tree's own shape.

Do NOT reach for a Zipper in these cases, and the reason matters more than
the rule.

- **The structure is mutated in place anyway.** If the surrounding
  program already treats the tree as a mutable object graph with parent
  pointers, a zipper adds an immutable overlay on top of a design that
  gains nothing from immutability. A doubly linked structure with real
  parent pointers solves the same navigation problem more directly inside
  a mutable design, at the cost of the sharing and undo benefits a zipper
  gives up front.
- **Access is by key or index, not by position.** A balanced search tree,
  a hash map, or an array accessed by integer index does not benefit from
  a zipper, because the caller already knows where it is going in one
  step. Building a zipper first, only to move to a known index, is
  strictly slower than an indexed lookup.
- **The structure is visited once, root to leaves, with no backtracking.**
  A single depth-first fold or map needs no cursor to remember, because
  the call stack of the traversal function already plays that role. A
  zipper earns its cost only when the caller needs to return to a
  position later, or hold several positions at once.
- **The tree is enormous and mostly untouched by any single session.** A
  zipper still holds the full path from the root to the focus in memory.
  For a structure so large that even that path is expensive, a database
  cursor or an external index that does not materialise the path is the
  honest shape.
- **The language has cheap, safe, in-place mutation with sound aliasing
  rules already, and no requirement for undo or sharing.** Rust is the
  sharp case, see the language note in dimension 8. An index-backed pool
  of nodes with a small integer cursor frequently outperforms and
  outsimplifies a translated zipper there.
- **The structure has cycles or is not a tree at all.** The classical
  zipper assumes a tree or a list, both acyclic. A cyclic graph has no
  well defined "context above the focus" in the same sense, and a zipper
  built naively over a graph either duplicates shared subtrees or loses
  the cycle. A different technique, generally an explicit visited set, is
  needed there.

## 5. Structure

Two participants, named by the role they play, whose combination is the
zipper value itself.

- **Focus.** The subtree currently under attention. In the classical
  construction this is a value of the same type as the whole structure,
  so any operation defined on the whole structure also applies directly
  to the focus.
- **Context.** Everything that is not the focus, represented as an
  ordered stack of frames, one per level of ancestry from the focus back
  to the root. Each frame records the parent's own label or data, the
  siblings that came before the focus at that level (usually reversed for
  O(1) access to the nearest one), and the siblings that come after.

A zipper value is the pair of Focus and Context. Moving down pushes a new
frame recording the current node's siblings and pops the chosen child out
as the new focus. Moving up pops the top frame and rebuilds the parent
node from the popped siblings plus the current focus, which becomes the
new focus. Moving left or right shifts one element between the two
sibling lists inside the top frame without touching any frame below it.
Editing replaces the focus with a new value and leaves every frame
untouched. Only a walk back to the root, when the caller finally wants the
whole edited structure, rebuilds the ancestors, and it rebuilds exactly
the ones on the path, nothing else.

## 6. ASCII structure diagram

```
    Whole tree, focus on node D                Zipper representation

    A                                          Focus:  D
    +-- B                                              (its own children,
    |   +-- D  (focus)                                  if any, untouched)
    |   +-- E
    +-- C                                       Context, one frame per level:

                                                 Frame 0 (children of B)
                                                   left siblings:  []
                                                   parent label:   B
                                                   right siblings: [E]

                                                 Frame 1 (children of A)
                                                   left siblings:  []
                                                   parent label:   A
                                                   right siblings: [C]

   Reading the context bottom to top rebuilds the path back to the root.
   Reading it top to bottom is the order frames are pushed while
   descending from the root to the current focus.
```

## 7. Dynamics

The runtime flow below shows a focus moving down into a child, sideways to
a sibling, an edit at the new focus, and a walk back up rebuilding the
ancestors along the way.

```
Caller            Zipper(focus, ctx)          New zipper values

|-- down(zip on A) ------------------->|
|                                       |-- push frame for A's siblings
|                                       |-- pop first child B as focus
|<-- zip(focus=B, ctx=[frame:A]) ------|

|-- right(zip on B) -------------------->|
|                                        |-- shift B into left siblings
|                                        |-- pop next child D as focus
|<-- zip(focus=D, ctx=[frame:A, frame:B])|

|-- edit(zip, D') ----------------------->|
|                                         |-- replace focus only, no
|                                         |   frame is touched
|<-- zip(focus=D', ctx=[frame:A, frame:B])|

|-- up(zip) ------------------------------>|
|                                          |-- pop frame:B, rebuild B'
|                                          |   from D' plus B's siblings
|<-- zip(focus=B', ctx=[frame:A]) --------|

|-- up(zip) ------------------------------>|
|                                          |-- pop frame:A, rebuild A'
|                                          |   from B' plus A's siblings
|<-- zip(focus=A', ctx=[]) ---------------|

|-- top-level tree is A' -------------------------------------->|
```

Each arrow allocates a small, constant amount of new structure. the tree
below the focus, and every part of the tree not on the current path, is
never copied and is shared by reference with the tree the zipper was
built from.

## 8. Implementation variants

**Direct tree zipper, hand written per shape.** The classical Huet
construction, written once for a specific tree type with a hand written
context type that mirrors that tree's constructors. This is the clearest
form to learn from and the one Huet's own paper presents, and it is the
right choice when only one or two tree shapes need a cursor.

**Generic zipper via type derivatives.** Following McBride 2001, the
one-hole context type for a data type can be derived mechanically from
the type's own definition using the rules of formal differentiation over
sums and products. a sum type differentiates to a choice of which branch
holds the hole, and a product type differentiates to a choice of which
factor holds the hole times the untouched other factors. Libraries in
typed functional languages that support generic programming, such as
Haskell's generics-sop or a Template Haskell derivation, generate the
context type for an arbitrary data type this way, so the zipper for a new
tree shape needs no hand written context.

**List zipper, the degenerate case.** A list has one recursive position
per node instead of a branching set, so its context collapses to a single
reversed prefix list plus the unvisited suffix. This is the shape used
for a text editor buffer, where the focus is the character or line at the
cursor and the two lists are the text before and after it. It is worth
naming separately because it is the shape most programmers meet first,
often without recognising it as a zipper at all.

**Dynamic, untyped zipper over a generic node representation.** Instead
of a context type written per tree shape, the context is represented
uniformly as a stack of generic frames, each holding a node's tag, its
already visited children, and its not yet visited children, all stored as
values of one common type rather than as distinct Haskell or ML
constructors. Clojure's clojure.zip namespace takes this shape, working
over any structure the caller supplies branch, children, and make-node
functions for, which is why it works unmodified on vectors, on Clojure's
own persistent maps treated as nested structures, and on XML, see
dimension 9. The price is that the shape of the context is no longer
checked by the type system, so a caller can attempt an operation the
underlying structure does not support and only find out at runtime.

**Zipper as a specialised list-of-choices, for a homogeneous rose tree.**
When every node has the same shape, an ordered sequence of children with
no other fields, the context frame reduces to exactly two lists of
siblings and nothing else, dropping the per-shape complexity of the
generic derivative construction while staying general across any rose
tree. This is the shape a window manager or a document outline commonly
uses.

**Language note on Rust.** Rust's ownership model resists the classical
zipper directly, because rebuilding a parent from a moved-out child and a
stack of frames means repeatedly taking ownership of pieces of a tree and
handing new pieces back, which the borrow checker does not make free the
way a garbage collected language does. The idiomatic Rust answer to the
same navigation problem is usually a pool of all nodes stored in one
`Vec` and addressed by integer index, with a cursor that is only an
index plus a small stack of sibling indices. This gives the same
O(depth) movement and edit cost as a zipper, without the ownership
friction, at the cost of losing the automatic structural sharing a
persistent zipper gets for free, an index-based tree is usually
rebuilt in place rather than shared between an old and a new version.
This entry counts that as the language's own idiomatic translation of
the pattern's intent rather than as the same implementation, and no Rust
code sample is included for that reason.

## 9. Known production uses

**Clojure `clojure.zip`.** The standard library namespace `clojure.zip`
implements a generic, dynamically typed zipper over any structure for
which the caller supplies branch, children, and make-node functions, and
exposes navigation functions `down`, `up`, `left`, `right`, `next`,
`prev`, `leftmost`, `rightmost`, edit functions `edit`, `replace`,
`insert-child`, `insert-left`, `insert-right`, `remove`, and
reconstruction functions `root` and `node`, plus ready-made constructors
`seq-zip`, `vector-zip`, and `xml-zip` for the common cases. Clojure
`clojure.zip` API documentation,
https://clojure.github.io/clojure/clojure.zip-api.html, verified
2026-08-21.

**XMonad `XMonad.StackSet`.** The XMonad window manager represents the
set of workspaces and the stack of windows on each workspace as a value
whose navigation follows Huet's construction directly, so that shifting
focus, inserting a window next to the current one, and reversing the
window order are all constant time operations with no possibility of an
out of bounds index while the currently focused window is tracked. The
module's own documentation states the design follows the zipper. Hackage
package documentation, `xmonad`, module `XMonad.StackSet`,
https://hackage.haskell.org/package/xmonad/docs/XMonad-StackSet.html,
verified 2026-08-21.

**Haskell `rosezipper`.** A general purpose zipper over `Data.Tree`'s
rose trees, published as an independent Hackage package, giving the same
up, down, left, right, and edit vocabulary over any tree built from
`Data.Tree`'s `Node` constructor without a caller having to hand write
the context type for that shape. Hackage package documentation,
`rosezipper`, https://hackage.haskell.org/package/rosezipper, verified
2026-08-21.

## 10. Consequences

Positive.

- Movement and edit near an already visited position cost time
  proportional to the depth of the cursor, not the size of the whole
  structure.
- The original structure, and every zipper value built from it earlier in
  the program, stay valid and unchanged after an edit, which gives undo,
  redo, and safe concurrent readers for free.
- The part of the structure away from the current path is shared by
  reference between the old and new versions, so the memory cost of one
  local edit is proportional to the depth of the edit, not the size of
  the tree.
- Traversal code reads as a sequence of plain function calls, up, down,
  left, right, with no manual index arithmetic and no explicit stack for
  the caller to maintain.
- The construction generalises mechanically to any recursively defined
  type, per McBride's derivative result, rather than needing to be
  reinvented by hand for every new shape.

Negative.

- Each step away from the root allocates one context frame, so a zipper
  held deep in a wide tree carries real memory overhead compared with a
  bare pointer into a mutable structure.
- The API surface is larger than plain field access, a caller must learn
  and correctly sequence up, down, left, right, edit, and a final
  rebuild.
- In a statically typed language with a heterogeneous tree, the context
  type for each node shape is itself a distinct type, which can multiply
  the number of types in a codebase unless a generic derivation is used.
- The pattern gives no benefit for random access by key or index, and
  building a zipper purely to reach one known position by index is
  strictly worse than an indexed lookup.
- A zipper assumes an acyclic tree or list. it does not translate cleanly
  to a graph with shared or cyclic structure without further design.

## 11. Failure modes and misuse

**Losing the tail of the walk.** Symptom. A caller calls `root` on a
zipper too early, before an intended edit further along the walk, and
the edit is silently lost because it was applied to a discarded zipper
value rather than the one that was rebuilt. Cause. Confusing the
zipper value, which is immutable, with a mutable cursor object, so an
edit is mistakenly treated as an in-place effect on a shared reference
rather than a value the caller must keep using. Fix. Always thread the
returned zipper value forward through every subsequent operation, the
same discipline any persistent data structure API requires.

**Rebuilding on every step instead of only at the end.** Symptom. A
traversal that visits many nodes runs far slower than expected, with
profiling showing repeated tree reconstruction. Cause. Calling `root`,
or an equivalent "materialise the whole tree" operation, inside a loop
that also keeps moving the cursor, so every step pays the full rebuild
cost instead of paying it once when the caller is actually done. Fix.
Call the whole-tree reconstruction exactly once, after the walk and all
edits are complete.

**Context type explosion in a typed language.** Symptom. A codebase
accumulates one hand written context type per tree node variant, and
every new node shape added to the tree requires a matching new context
type, so a small tree grammar change becomes a large, tedious patch.
Cause. Choosing the direct, hand written zipper variant, dimension 8, for
a tree with many distinct node shapes. Fix. Move to a generically
derived zipper, or to the dynamic untyped variant, when the number of
distinct node shapes grows past a handful.

**Attempting a move past the edge without checking.** Symptom. A
runtime error or an exception when calling `left` at the leftmost
sibling, or `up` at the root. Cause. Treating navigation as always
succeeding, rather than as a partial operation that can fail at a
structural boundary. Fix. Movement functions should return an explicit
"cannot move" result, `None`, `null`, or an option type, and callers
check it, the same discipline any partial function needs.

**Zipper over a structure that is secretly mutated elsewhere.** Symptom.
A zipper built from a tree produces edits that appear to vanish, or
produces a rebuilt tree that does not match what the caller expected.
Cause. Something else in the program mutated the underlying structure,
or a node inside it, after the zipper was built, breaking the assumption
that the shared, untouched parts of the tree are stable. Fix. Enforce
that the structure the zipper walks is genuinely immutable end to end,
which is the same requirement the persistent-data-structures entry in
this family states generally.

**Using a zipper as a substitute for an index.** Symptom. A hot path that
repeatedly builds a fresh zipper, walks straight to a known position by
index, reads one value, and discards the zipper, runs noticeably slower
than a direct indexed lookup would. Cause. Reaching for the pattern by
habit rather than because the access pattern is actually a sequence of
nearby moves. Fix. Use direct indexed access when the position is
already known, and reserve the zipper for genuinely relative,
step by step navigation.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Zipper | Mutable tree with parent pointers | Path-copying without a cursor | Iterator over an immutable structure | Index-backed node pool |
|---|---|---|---|---|---|
| Cost of a local edit | O(depth) | O(1) | O(depth) per edit, no reuse across edits | Not applicable, read only | O(1) |
| Cost of a move to a neighbour | O(1) | O(1) | Requires rebuilding a fresh path each time | O(1) forward only, no backtracking | O(1) |
| Immutability of the original structure | Preserved | Broken, in place mutation | Preserved | Preserved | Broken, in place mutation |
| Structural sharing between versions | Automatic | Not applicable, one mutable copy | Only if the caller manually reuses the cursor | Not applicable | Not applicable, one mutable copy |
| Undo and branching exploration | Free, every earlier zipper value is still valid | Requires a manual snapshot mechanism | Free, if the caller retains earlier cursors | Not applicable | Requires a manual snapshot mechanism |
| Type complexity in a statically typed language | High for a hand written per-shape context | Low, plain fields | Low | Low | Low |
| Aliasing safety in Rust | Awkward, fights the borrow checker | Requires unsafe or Rc RefCell | Better, still requires care | Good | Good, the idiomatic Rust shape |
| Random access by key | Poor, must walk | Good, with an index alongside | Poor | Poor | Good, direct index |

Reading of the table. A zipper wins where the access pattern is a
sequence of nearby moves and edits over an immutable structure and the
caller wants undo or sharing for free. A mutable tree with parent
pointers wins when immutability, sharing, and undo are not required and
raw speed with no allocation matters more. Path-copying without a
persistent cursor wins only when edits are rare and isolated, because
without a cursor to reuse, each edit repeats the whole path rebuild. An
iterator wins for a single forward pass with no backtracking and no
edits. An index-backed node pool wins in a language, chiefly Rust,
where ownership makes the classical zipper's rebuild-from-borrowed-pieces
shape expensive to express safely.

## 13. Related and incompatible patterns

- **Persistent Data Structures.** The umbrella this pattern belongs to. A
  zipper is a persistent data structure specialised for cursor movement
  and local edits, built out of the same never mutate, always share
  discipline the family entry describes generally.
- **Structural Sharing.** The mechanism, not the shape. Every zipper
  operation relies on structural sharing to keep the untouched parts of
  the tree unchanged and shared by reference, which is the entry this
  pattern leans on for its memory and performance behaviour.
- **Lens.** A complementary focusing technique at a different grain. A
  lens focuses on one field inside a fixed, statically known type and
  composes with other lenses to reach a deeply nested field. A zipper
  focuses on one position inside a recursively defined structure of
  unknown depth and moves relative to that position. Some libraries
  build a zipper-like traversal on top of lens-family abstractions for
  exactly this reason, treating the zipper as a lens that also knows how
  to move sideways.
- **Iterator.** Solves the read-only, forward-only case of a similar
  problem. An iterator that only needs `next` and never needs to go
  back, insert, or replace at the current position can use a plain
  iterator and skip a zipper's extra structure entirely.
- **Immutability.** The prerequisite. A zipper's sharing and undo
  benefits depend entirely on the tree it walks staying immutable, so
  the two patterns are always used together, never as alternatives.
- **In-place tree mutation with raw parent pointers.** Conflicts
  directly. A tree that also maintains real, mutable back pointers from
  child to parent solves the same "how do I get back up" problem the
  zipper's context stack solves, but it does so by breaking the value
  semantics a zipper exists to preserve, and the two approaches should
  not be combined on the same structure.
- **Shared mutable tree accessed from multiple threads.** Actively
  conflicts. A zipper's guarantees rest on nobody mutating the
  underlying nodes out from under it. A tree that is also shared and
  mutated concurrently invalidates that assumption regardless of how
  carefully the zipper code itself is written.

## 14. Refactoring path in and out

Introducing the pattern into code that does not have it. Ordered steps.

1. Identify the recursive traversal that currently rebuilds the whole
   structure, or mutates it in place, on every edit. Confirm the access
   pattern is genuinely a sequence of nearby moves rather than isolated,
   unrelated lookups, otherwise a zipper is the wrong fix, see dimension
   4.
2. Define the context frame type for the structure's shape. start with
   the direct, hand written variant from dimension 8 for a single tree
   shape, since it is the easiest to verify against Huet's own
   construction.
3. Write the four core navigation functions, down, up, left, right, each
   returning an explicit "cannot move" result at a structural boundary
   rather than throwing.
4. Write edit and replace as pure functions over the focus only, and
   confirm by inspection that neither touches any context frame.
5. Write root, the function that walks all the way up, rebuilding every
   ancestor along the path, and confirm it is called exactly once per
   completed walk in the calling code, not on every step, per the
   failure mode in dimension 11.
6. Replace the old traversal's manual index or pointer bookkeeping with
   calls to the new navigation functions, one call site at a time,
   keeping the old code path available until the new one is verified on
   the same inputs.
7. If the tree grows more node shapes over time and the number of hand
   written context types becomes a maintenance burden, move to the
   generically derived variant from dimension 8.

Removing the pattern when it stops earning its place. Signals that it
should go include a call site that only ever moves straight to one known
position by index and never backtracks, or a hot path profiled to spend
real time in the zipper's own allocation rather than in the caller's
logic.

1. Confirm every call site genuinely uses relative movement, not only a
   single known-index lookup dressed up as a walk. If some call sites do
   the latter, migrate those specific sites to direct indexed access
   first.
2. Where undo or sharing is not actually used by any caller, this is the
   strongest signal the pattern is unearned, since that benefit is most
   of what a zipper buys over a plain mutable cursor.
3. Replace the zipper's navigation calls with the target representation's
   own access, an index step into a node pool, or a mutable parent
   pointer walk, one call site at a time, keeping tests green after each
   site.
4. Delete the context frame types and the navigation functions only after
   no call site references them.

## 15. Testing and verification

Easier because of the pattern.

- Every zipper value is an ordinary immutable value, so a test can build
  one, perform a sequence of moves and edits, and assert on the exact
  resulting zipper without any setup or teardown of shared mutable
  state.
- Because earlier zipper values remain valid after later edits, a test
  can hold a "before" zipper and an "after" zipper side by side and
  assert on both, which is awkward or impossible to express safely
  against a mutable tree with parent pointers.
- Property tests are a natural fit. round tripping down then up should
  return an equal tree to the one before the descent, and root after any
  sequence of moves with no edits should equal the original tree. These
  are exactly the kind of universally quantified, mechanically checkable
  invariants a property test framework is built for.

Harder because of the pattern.

- A boundary condition, moving left at the leftmost sibling or up at the
  root, needs its own explicit test per navigation function, since these
  are exactly the cases most likely to be mishandled, per the failure
  mode in dimension 11.
- Testing the generically derived variant from dimension 8 requires
  either trusting the generic derivation mechanism or writing a
  reference implementation to compare it against for at least one
  concrete tree shape.

Techniques that apply.

- **Round trip property.** For an arbitrary tree and an arbitrary valid
  sequence of moves with no edits along the way, assert that `root`
  after the sequence equals the tree before it. This is the single most
  valuable test for a new zipper implementation, because it exercises
  every navigation function's bookkeeping at once.
- **Edit and rebuild property.** For an arbitrary tree, an arbitrary
  position, and an arbitrary new value, assert that editing at that
  position and calling `root` produces a tree identical to a reference
  "rebuild the whole tree by hand" implementation, and that every part of
  the tree away from the edited position is reference-equal, not merely
  value-equal, to the corresponding part of the original tree, which
  verifies structural sharing actually happened rather than merely
  producing the right value by accident.
- **Boundary table.** A small table-driven test enumerating every
  structural boundary, leftmost, rightmost, root, leaf, asserting each
  navigation function returns the explicit "cannot move" result there
  rather than an exception.
- **Old zipper still valid after an edit.** A direct regression test
  building a zipper, taking a snapshot reference to it, performing an
  edit that returns a new zipper, then asserting the snapshot's own
  `root` still equals the original, unedited tree.

## 16. Observability signals

The pattern is internal machinery inside a single call's traversal, so it
rarely needs dedicated production telemetry of its own, but two signals
are worth adding where a zipper drives a hot or user-facing path.

What to record.

- A counter or histogram of the depth reached during a walk, labelled by
  the call site, when the same zipper code is used across structures of
  widely varying depth, such as a general purpose syntax tree editor.
  Depth is the direct proxy for both movement cost and context frame
  memory, so a shift in the distribution flags either a change in the
  data being walked or a bug that fails to terminate a descent.
- A counter of "cannot move" results returned at a structural boundary,
  labelled by which navigation function produced it. A sudden rise
  points either at a caller bug attempting moves it should have guarded
  against, or at unexpectedly shallow or narrow input data reaching the
  code path.

A healthy instance on a dashboard. Depth stays within the range the
input data is expected to have, and the boundary-result counter stays
near zero or matches a known, intentional pattern such as an editor UI
that always tries `left` once before deciding whether to disable a
button.

A failing instance. Depth grows without bound over the life of a long
running process, which points at a leaked reference retaining a deep
zipper value rather than letting it be collected once the walk that
built it is done. Or the boundary-result counter climbs sharply after a
deploy, which usually means an upstream change started feeding
shallower or narrower trees than the navigation code assumes.

## 17. Security and privacy implications

The pattern is close to silent on security in its ordinary use, operating
entirely over data already resident in memory inside one process, and
inventing a specific attack surface here would be dishonest. Two
practical implications are worth naming.

**Memory exhaustion from unbounded depth.** Because every step away from
the root allocates a context frame, and none of those frames are freed
until the caller stops referencing the zipper, a walk driven by
attacker-controlled input, an arbitrarily deep nested document format
parsed straight into a tree and then walked with a zipper, can be made to
allocate proportionally to that attacker-chosen depth. Bound the maximum
depth a zipper-driven walk will follow before it started from untrusted
input, the same discipline any recursive descent over untrusted input
needs regardless of whether a zipper is involved.

**Stale references after a claimed deletion.** Because a zipper value
keeps every earlier version of the tree reachable through its own
context and focus for as long as the caller holds that zipper value, a
caller that believes deleting a node from the "current" tree has removed
sensitive data from memory can be wrong if an older zipper value, still
referencing the pre-deletion tree, is retained somewhere else in the
program. Where a deletion is meant to remove sensitive data from
reachable memory, confirm every zipper value derived from the
pre-deletion tree is also dropped, not only the one the caller most
recently built.

On privacy the pattern is neutral in itself. it holds exactly the data
the structure it walks already holds, and adds no new persistence,
network, or logging surface of its own.

## Code examples

Three languages where the pattern is genuinely idiomatic in different
ways. TypeScript shows the direct, hand written variant over a small rose
tree, using a discriminated union for the context frame the way a
statically typed language with algebraic data types naturally expresses
it. Python shows the dynamic, generic variant in the style of Clojure's
`clojure.zip`, working over any tree the caller describes with a small
protocol of functions, closer to how the pattern reads in a dynamically
typed language. Go shows the same direct construction as the TypeScript
version but without algebraic data types, using a single struct with an
explicit label field for the tree and a slice-backed context, the shape
the pattern takes in a language with garbage collection, value-typed
structs, and no sum types. Java is omitted, because a faithful, idiomatic
translation of either variant into Java needs either sealed interfaces
with pattern matching, which read closer to the TypeScript version once
written out, or a general purpose visitor and reflection based context,
which reads closer to the Python version, so it would not add a fourth
genuinely distinct shape within the length this entry has room for. Rust
is intentionally omitted, per the language note in dimension 8.

### TypeScript

```typescript
type Tree = { label: string; children: Tree[] };

type Frame = {
  parentLabel: string;
  leftSiblings: Tree[];
  rightSiblings: Tree[];
};

type Zipper = { focus: Tree; context: Frame[] };

function fromTree(t: Tree): Zipper {
  return { focus: t, context: [] };
}

function down(z: Zipper): Zipper | null {
  const [first, ...rest] = z.focus.children;
  if (first === undefined) return null;
  const frame: Frame = {
    parentLabel: z.focus.label,
    leftSiblings: [],
    rightSiblings: rest,
  };
  return { focus: first, context: [frame, ...z.context] };
}

function right(z: Zipper): Zipper | null {
  const [frame, ...rest] = z.context;
  if (frame === undefined) return null;
  const [next, ...remaining] = frame.rightSiblings;
  if (next === undefined) return null;
  const newFrame: Frame = {
    parentLabel: frame.parentLabel,
    leftSiblings: [z.focus, ...frame.leftSiblings],
    rightSiblings: remaining,
  };
  return { focus: next, context: [newFrame, ...rest] };
}

function up(z: Zipper): Zipper | null {
  const [frame, ...rest] = z.context;
  if (frame === undefined) return null;
  const children = [
    ...frame.leftSiblings.slice().reverse(),
    z.focus,
    ...frame.rightSiblings,
  ];
  const parent: Tree = { label: frame.parentLabel, children };
  return { focus: parent, context: rest };
}

function edit(z: Zipper, newFocus: Tree): Zipper {
  return { focus: newFocus, context: z.context };
}

function root(z: Zipper): Tree {
  let cur = z;
  while (cur.context.length > 0) {
    const next = up(cur);
    if (next === null) break;
    cur = next;
  }
  return cur.focus;
}

const tree: Tree = {
  label: "root",
  children: [
    { label: "a", children: [] },
    { label: "b", children: [] },
  ],
};

let z = fromTree(tree);
z = down(z)!;
z = right(z)!;
z = edit(z, { label: "b-renamed", children: [] });
console.log(JSON.stringify(root(z)));
```

### Python

```python
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Tree:
    label: str
    children: tuple["Tree", ...] = ()


@dataclass(frozen=True)
class Frame:
    parent_label: str
    left: tuple[Tree, ...]
    right: tuple[Tree, ...]


@dataclass(frozen=True)
class Zipper:
    focus: Tree
    context: tuple[Frame, ...] = field(default_factory=tuple)


def zip_down(z: Zipper) -> Zipper | None:
    if not z.focus.children:
        return None
    first, *rest = z.focus.children
    frame = Frame(z.focus.label, (), tuple(rest))
    return Zipper(first, (frame, *z.context))


def zip_right(z: Zipper) -> Zipper | None:
    if not z.context:
        return None
    frame, *rest = z.context
    if not frame.right:
        return None
    nxt, *remaining = frame.right
    new_frame = Frame(frame.parent_label, (z.focus, *frame.left), tuple(remaining))
    return Zipper(nxt, (new_frame, *rest))


def zip_up(z: Zipper) -> Zipper | None:
    if not z.context:
        return None
    frame, *rest = z.context
    children = (*reversed(frame.left), z.focus, *frame.right)
    parent = Tree(frame.parent_label, children)
    return Zipper(parent, tuple(rest))


def zip_edit(z: Zipper, new_focus: Tree) -> Zipper:
    return Zipper(new_focus, z.context)


def zip_root(z: Zipper) -> Tree:
    cur = z
    while cur.context:
        nxt = zip_up(cur)
        if nxt is None:
            break
        cur = nxt
    return cur.focus


if __name__ == "__main__":
    tree = Tree("root", (Tree("a"), Tree("b")))
    z: Zipper | None = Zipper(tree)
    z = zip_down(z)
    z = zip_right(z)
    z = zip_edit(z, Tree("b-renamed"))
    print(zip_root(z))
```

### Go

```go
package main

import "fmt"

type Tree struct {
	Label    string
	Children []Tree
}

type Frame struct {
	ParentLabel string
	Left        []Tree
	Right       []Tree
}

type Zipper struct {
	Focus   Tree
	Context []Frame
}

func FromTree(t Tree) Zipper {
	return Zipper{Focus: t}
}

func (z Zipper) Down() (Zipper, bool) {
	if len(z.Focus.Children) == 0 {
		return Zipper{}, false
	}
	first := z.Focus.Children[0]
	rest := append([]Tree{}, z.Focus.Children[1:]...)
	frame := Frame{ParentLabel: z.Focus.Label, Right: rest}
	return Zipper{Focus: first, Context: append([]Frame{frame}, z.Context...)}, true
}

func (z Zipper) Right() (Zipper, bool) {
	if len(z.Context) == 0 || len(z.Context[0].Right) == 0 {
		return Zipper{}, false
	}
	frame := z.Context[0]
	next := frame.Right[0]
	remaining := append([]Tree{}, frame.Right[1:]...)
	newLeft := append([]Tree{z.Focus}, frame.Left...)
	newFrame := Frame{ParentLabel: frame.ParentLabel, Left: newLeft, Right: remaining}
	return Zipper{Focus: next, Context: append([]Frame{newFrame}, z.Context[1:]...)}, true
}

func (z Zipper) Up() (Zipper, bool) {
	if len(z.Context) == 0 {
		return Zipper{}, false
	}
	frame := z.Context[0]
	children := make([]Tree, 0, len(frame.Left)+1+len(frame.Right))
	for i := len(frame.Left) - 1; i >= 0; i-- {
		children = append(children, frame.Left[i])
	}
	children = append(children, z.Focus)
	children = append(children, frame.Right...)
	parent := Tree{Label: frame.ParentLabel, Children: children}
	return Zipper{Focus: parent, Context: z.Context[1:]}, true
}

func (z Zipper) Edit(newFocus Tree) Zipper {
	return Zipper{Focus: newFocus, Context: z.Context}
}

func (z Zipper) Root() Tree {
	cur := z
	for len(cur.Context) > 0 {
		next, ok := cur.Up()
		if !ok {
			break
		}
		cur = next
	}
	return cur.Focus
}

func main() {
	tree := Tree{Label: "root", Children: []Tree{
		{Label: "a"},
		{Label: "b"},
	}}
	z := FromTree(tree)
	z, _ = z.Down()
	z, _ = z.Right()
	z = z.Edit(Tree{Label: "b-renamed"})
	fmt.Println(z.Root())
}
```

## 18. References

1. Gerard Huet. "The Zipper". *Journal of Functional Programming*, volume
   7, issue 5, pages 549 to 554, September 1997.
   https://www.st.cs.uni-saarland.de/edu/seminare/2005/advanced-fp/docs/huet-zipper.pdf
   Verified 2026-08-21. Source of the original construction, the name,
   the location terminology, and the seam metaphor.
2. Conor McBride. "The Derivative of a Regular Type is its Type of
   One-Hole Contexts" (extended abstract). 2001.
   http://strictlypositive.org/diff.pdf
   Verified 2026-08-21. Source for the derivative connection and the
   generic derivation of a zipper's context type in dimension 8.
3. Wikipedia contributors. "Zipper (data structure)".
   https://en.wikipedia.org/wiki/Zipper_(data_structure)
   Verified 2026-08-21. Used only to confirm common phrasing, not as a
   source of explanation.
4. Clojure. `clojure.zip` API documentation.
   https://clojure.github.io/clojure/clojure.zip-api.html
   Verified 2026-08-21. Source for the dynamic, generic zipper variant
   in dimension 8 and the production use in dimension 9.
5. Hackage. `xmonad` package documentation, module `XMonad.StackSet`.
   https://hackage.haskell.org/package/xmonad/docs/XMonad-StackSet.html
   Verified 2026-08-21. Source for the XMonad production use in
   dimension 9.
6. Hackage. `rosezipper` package documentation.
   https://hackage.haskell.org/package/rosezipper
   Verified 2026-08-21. Source for the general purpose rose-tree zipper
   production use in dimension 9.
