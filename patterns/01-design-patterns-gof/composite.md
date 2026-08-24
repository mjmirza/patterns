---
name: Composite
slug: composite
family: 01-design-patterns-gof
category: Structural
aliases: [Part-Whole Hierarchy, Recursive Composition, Object Tree]
first_described: "Gamma, Helm, Johnson, Vlissides 1994"
maturity: canonical
related: [decorator, iterator, visitor, chain-of-responsibility, flyweight, interpreter, builder]
incompatible_with: []
verified: 2026-08-02
---

# Composite

## 1. Name, aliases, and lineage

The canonical name is Composite. It is one of the seven structural patterns in
the Gang of Four catalog, described in Erich Gamma, Richard Helm, Ralph Johnson
and John Vlissides, *Design Patterns. Elements of Reusable Object-Oriented
Software*, Addison-Wesley, 1994, chapter 4 (Structural Patterns), Composite,
beginning at page 163. The stated intent is to compose objects into tree
structures that represent part-whole hierarchies, so that clients can treat
individual objects and compositions of objects uniformly
([Wikipedia summary of the GoF intent](https://en.wikipedia.org/wiki/Composite_pattern),
verified 2026-08-02).

Three aliases appear in real use and each carries a slightly different emphasis.

- **Part-Whole Hierarchy.** The phrase the GoF book itself uses in the intent.
  It emphasises the domain relationship rather than the code shape, and it is
  the phrasing that shows up in modelling and domain-driven design writing.
- **Recursive Composition.** Common in functional and compiler literature, where
  the emphasis falls on the type being defined in terms of itself. An expression
  tree is recursive composition whether or not anybody calls it a Composite.
- **Object Tree.** The colloquial name used by framework documentation. The DOM
  calls its instance a node tree, Flutter calls its instance a widget tree, and
  React calls its instance a component tree. All three are Composite instances
  and none of the three uses the pattern name.

Two things are frequently mislabelled as Composite and are not.

- **A plain container class.** A `List<Order>` holds many orders. That is
  aggregation, not Composite, because the list is not itself an `Order`. The
  defining property of Composite is that the container satisfies the same
  interface as the thing it contains, so a container can be passed anywhere a
  single element can. Remove that property and the pattern is gone.
- **An inheritance hierarchy with depth.** A three-level class hierarchy is not
  a Composite. Composite is about the runtime object graph, not the compile-time
  type graph. A Composite normally has a shallow type hierarchy, often three
  types, and an arbitrarily deep object graph.

There is a lineage note worth recording. In the algebraic data type tradition,
the same structure is expressed as a sum type with a recursive constructor, for
example a `Tree` that is either a `Leaf` carrying a value or a `Node` carrying a
list of `Tree`. The object-oriented Composite and the algebraic recursive sum
type describe the same data. They differ in which axis is open to extension,
which is the Expression Problem, and dimension 13 returns to that difference
because it decides whether Composite plus Visitor is a good idea in a given
codebase.

## 2. Problem and context

There is a domain where a thing can be made of the same kind of thing, without
limit, and client code has to operate over the whole structure without caring how
deep it goes.

The situation reads like this in a codebase. There is an interface with an
operation, say `price()` or `render()` or `evaluate()`. Some implementations are
terminal, and one implementation holds a list of others. Every client that wants
a total, a rendering or a result has to know which case it has, so the code fills
with type tests. A function that sums prices starts as a loop over items, then
grows a branch for bundles that recurses, then grows a second branch for
promotional bundles containing bundles. The branching does not live in one place.
It reappears in the pricing service, in the export writer, in the audit report,
and in three tests. Each new client rediscovers the same recursion and gets it
subtly wrong in a different way.

Concretely, the shapes that produce this problem look like the following.

- A file system where a directory contains files and other directories, and a
  size calculation must cover both.
- A graphical scene where a group contains shapes and other groups, and drawing,
  hit testing and bounding box calculation must cover both.
- An organisation chart where a department contains employees and sub
  departments, and headcount and salary cost must cover both.
- An expression grammar where a binary operation contains two expressions, each
  of which may itself be a binary operation, and evaluation must cover both.
- A permission rule where an `AllOf` rule contains other rules, and evaluation
  must cover both.

The context that makes Composite the right answer has four parts, and all four
matter.

- **The recursion is genuinely in the domain**, not an artefact of one algorithm.
  A directory really does contain directories. If the nesting is a property of
  one report rather than of the data, the recursion belongs in the report.
- **The interesting operations make sense on both a part and a whole.** `size()`
  says something true for a file and for a directory. If half the operations mean
  nothing on one side, the abstraction is being forced.
- **Clients should not know the depth.** If every caller already knows it is
  handling exactly two levels, the pattern buys nothing and costs indirection.
- **The structure is a tree, or a directed acyclic graph that is treated as a
  tree.** Composite has no cycle handling of its own. Dimension 11 covers what
  happens when this assumption is violated, and it is the single most damaging
  failure mode the pattern has.

Outside that context Composite becomes an anti-pattern, and dimension 4 says why.

## 3. Forces

The pattern balances the following competing pressures.

- **Client simplicity.** Strongly favoured. This is the reason the pattern
  exists. A client writes one call against one interface and the structure
  handles its own recursion. Conditional logic over node kinds disappears from
  every client at once, which is the payoff that justifies the rest of the costs.
- **Type safety.** Sacrificed in the form the GoF book recommends. Declaring
  `add` and `remove` on the shared interface means a leaf must reject them at
  runtime rather than at compile time. Dimension 8 gives both forms and a
  recommendation, because this is the central design decision of the pattern.
- **Coupling.** Favoured between client and structure, since the client depends
  only on the shared interface. Mildly sacrificed inside the structure, because a
  composite couples itself to the shared interface of its children, which means
  the interface becomes hard to change once external code implements it.
- **Cognitive load.** Mixed, and this is the honest answer. Reading a single
  operation gets easier, because the composite implementation is usually three
  lines. Reasoning about a whole run gets harder, because control flow follows
  data shape rather than source order, and no source line tells you how deep the
  call will go.
- **Latency.** Sacrificed, and the amount is not small. A composite operation
  costs one virtual dispatch per node plus one iteration step per edge, and
  memory access follows pointer chasing rather than a contiguous scan. For a
  hundred nodes this is irrelevant. For a scene graph traversed sixty times a
  second, or a syntax tree of a million nodes, it is the largest single cost.
- **Stack depth.** Sacrificed by the naive implementation. Recursive traversal
  consumes one stack frame per level and a hostile or unlucky input can exhaust
  the stack. Dimension 8 gives the explicit stack form that removes this.
- **Consistency.** Favoured. Because there is one path through the structure,
  an operation applied to the root applies to everything exactly once, which
  removes a whole class of partial-update bugs.
- **Operability.** Sacrificed. A production incident in a composite structure
  produces a stack trace full of identical frames and an error that names a leaf
  without saying where in the tree that leaf sat. Dimension 16 covers the
  instrumentation that buys this back, and it is not optional once the trees grow
  large.
- **Cost of change.** Favoured for adding a node type, which touches nothing.
  Sacrificed for adding an operation, which touches every node type. That
  asymmetry is the Expression Problem, and it is why Visitor exists.
- **Team topology.** Favoured. A platform team owns the shared interface and the
  traversal primitives, and product teams add node types in their own modules
  without coordination. The seam is a published interface with a small surface.

A pattern that sacrificed nothing would be a language feature. Composite pays in
type safety, in per-node cost, and in the difficulty of adding an operation.

## 4. Applicability and non-applicability

Reach for Composite when the following hold.

- The domain contains a whole made of parts of the same kind, to arbitrary depth,
  and that recursion is stable rather than incidental.
- Clients want to apply an operation to a subtree without knowing its shape, and
  the same operation makes sense at every node.
- Node types are open, meaning new kinds of part will keep arriving, and adding
  one should not touch existing code.
- The structure is built once or rarely, and traversed often, so the pointer cost
  is amortised over many reads rather than paid on every write.
- The operation set is closed, or small enough that adding one to every node type
  is tolerable. If not, read the Visitor discussion in dimension 13 first.

Do NOT reach for Composite in these cases. This is the non-applicability list,
and the reason attached to each entry matters more than the entry.

- **The nesting is bounded and known.** An invoice has line items and line items
  do not have line items. Modelling that as a Composite adds a recursive
  abstraction over a two-level structure, and every reader then has to prove to
  themselves that the third level cannot occur. A plain list reads better and
  deletes cleanly. Cross reference the code smell family entry on speculative
  generality.
- **Leaves and composites share almost no real operations.** If the shared
  interface ends up holding one true method and five methods that throw on one
  side, the abstraction is a lie told to the type system. The uniformity that
  Composite promises has to be real uniformity in the domain, not uniformity
  manufactured by widening an interface until both sides fit.
- **The graph is not a tree and cycles are possible.** Composite has no cycle
  detection. A naive recursive traversal over a cyclic graph does not return, it
  overflows the stack. If the structure is a general graph, the pattern is the
  wrong starting point and a graph traversal with a visited set is the right one.
  Dimension 11 gives the failure in detail.
- **The traversal is performance critical and the tree is large.** A syntax tree
  of a million nodes traversed per keystroke, or a particle scene traversed per
  frame, will be limited by dispatch and cache misses rather than by the work
  itself. The answer there is a flat array with an index-based parent or child
  encoding, traversed with a loop. That is a data-oriented rewrite and it
  deliberately gives up the pattern.
- **The operation set is open and the node set is closed.** This is the mirror
  image of the case Composite handles well. When new operations arrive weekly and
  new node types never do, putting each operation on every node type means every
  new operation edits every existing class. Visitor inverts that, at the price of
  making new node types expensive. Choose by which axis actually moves.
- **The composite would exist only to hold configuration.** A "group" type whose
  sole job is to carry a name and a list, with no behaviour, is a container and
  should be modelled as one. The pattern is about shared behaviour, not shared
  nesting.
- **Persistence or serialisation is the primary concern.** Composite structures
  serialise badly in tabular stores and produce either recursive queries or a
  nested set encoding. If the main requirement is querying the structure rather
  than executing behaviour over it, model the relationship in the store first and
  let the object model follow, not the other way around.

## 5. Structure

Four participants, named by the role each plays.

- **Component.** The shared abstraction. It declares the operations that make
  sense on both a single element and a composition of elements. In the
  transparent form it also declares the child management operations, `add`,
  `remove` and `getChild`. Every client is written against this type and against
  nothing else. This is the only type the client is allowed to name, and holding
  that line is what makes the pattern pay.
- **Leaf.** A terminal node. It has no children and implements the domain
  operations directly. In the transparent form it must supply a rejecting
  implementation of the child management operations. There are normally many Leaf
  types and they carry the actual domain data.
- **Composite.** A node that holds an ordered or unordered collection of
  Components. It implements each domain operation by delegating to its children
  and combining the results, and it implements the child management operations
  for real. It normally holds children by the Component type only, so it can
  contain leaves and other composites without distinction, which is the property
  that makes depth unbounded.
- **Client.** Any code that manipulates objects through the Component interface.
  A client that reaches for `instanceof` or a type switch has stopped being a
  Client in the pattern sense, and that is the clearest sign the abstraction has
  failed.

Relationships. Composite holds a one-to-many association to Component, which is
the recursive edge and the whole structure of the pattern. Both Leaf and
Composite specialise Component. A parent back-reference from Component to its
parent is optional, discussed in dimension 8, and adds the ability to walk
upward at the cost of a cycle in the reference graph that complicates copying,
equality and garbage collection.

The combination rule inside a Composite operation carries more design weight than
it appears to. Summation, concatenation, boolean conjunction and maximum are all
monoid operations, and when the combination is a monoid the empty composite has a
well defined answer, which removes an entire family of null checks. When the
combination is not associative, or has no identity, the empty composite becomes a
special case that every operation has to handle separately, and that is a sign
the operation may not belong on the Component interface at all.

## 6. ASCII structure diagram

The transparent form, which is the form the GoF book recommends. Child management
is declared on Component, so a Leaf must reject it at runtime.

```
   +--------------------------------------+
   |             Component                |<--------+
   |--------------------------------------|         |
   | + operation(): Result                |         | children
   | + add(c: Component)      <-- unsafe  |         | (0..*)
   | + remove(c: Component)   <-- unsafe  |         |
   | + getChild(i: int): Component        |         |
   +--------------------------------------+         |
              ^                    ^                |
              |                    |                |
    implements|                    |implements      |
              |                    |                |
   +----------------------+   +--------------------------------+
   |        Leaf          |   |          Composite             |
   |----------------------|   |--------------------------------|
   | + operation()        |   | - children: List<Component> ---+
   | + add()   -> THROWS  |   | + operation()  (delegates)     |
   | + remove()-> THROWS  |   | + add(c)       (real)          |
   +----------------------+   | + remove(c)    (real)          |
                              +--------------------------------+

   Client ---- depends only on ----> Component
```

The safe form. Child management lives only on Composite, so the compiler rejects
`leaf.add(x)`, and the client must downcast to build or mutate the structure.

```
   +--------------------------------------+
   |             Component                |
   |--------------------------------------|
   | + operation(): Result                |     no child management here
   +--------------------------------------+
              ^                    ^
              |                    |
    implements|                    |implements
              |                    |
   +----------------------+   +--------------------------------+
   |        Leaf          |   |          Composite             |<-+
   |----------------------|   |--------------------------------|  |
   | + operation()        |   | - children: List<Component> -------+
   +----------------------+   | + operation()  (delegates)     |
                              | + add(c: Component)            |
                              | + remove(c: Component)         |
                              +--------------------------------+

   Client --- reads through ----> Component
   Client --- writes through ---> Composite  (needs the concrete type)
```

A tree instance, which is the diagram that actually explains the pattern to a
reader. This is a file system fragment where every box is a Component and the
total size at the root is produced by one call.

```
                 Composite: /project              size = 1 + 4 + 12 + 3 = 20
                 +---------------------+
                 |  children: 3        |
                 +----+-----+-----+----+
                      |     |     |
        +-------------+     |     +--------------------+
        |                   |                          |
   Leaf: README.md    Composite: src               Leaf: LICENSE
   +--------------+   +-----------------+          +--------------+
   | size = 1     |   | children: 2     |          | size = 3     |
   +--------------+   +--+-----------+--+          +--------------+
                         |           |
              +----------+           +----------+
              |                                 |
        Leaf: main.go                   Composite: util
        +----------------+              +-----------------+
        | size = 4       |              | children: 1     |
        +----------------+              +--------+--------+
                                                 |
                                          Leaf: strings.go
                                          +----------------+
                                          | size = 12      |
                                          +----------------+

   The client calls root.size() once. Depth 4 is invisible to the client.
```

## 7. Dynamics

The runtime flow has one property worth stating plainly. The client makes exactly
one call. Every subsequent call is made by the structure to itself, and the total
number of calls equals the number of nodes. The client cannot observe the depth,
the branching factor, or the order, unless the interface deliberately exposes it.

```
Client        /project(C)      README(L)      src(C)       main.go(L)   util(C)
  |                |               |             |              |          |
  |-- size() ----->|               |             |              |          |
  |                |-- size() ---->|             |              |          |
  |                |<-- 1 ---------|             |              |          |
  |                |                             |              |          |
  |                |-- size() ------------------>|              |          |
  |                |                             |-- size() --->|          |
  |                |                             |<-- 4 --------|          |
  |                |                             |-- size() -------------->|
  |                |                             |              |          |
  |                |                             |     (util recurses into |
  |                |                             |      strings.go, 12)    |
  |                |                             |<-- 12 ------------------|
  |                |<-- 16 (4 + 12) -------------|              |          |
  |                |                                                       |
  |                |-- size() --> LICENSE(L) --> 3                         |
  |                |                                                       |
  |<-- 20 ---------|                                                       |
  |                |                                                       |
```

Three timing notes.

First, the call stack depth at the deepest point equals the height of the tree
plus one, not the node count. A wide shallow tree is cheap on the stack and a
narrow deep tree is expensive. A linked-list-shaped tree, which happens when a
parser produces a left-leaning chain from a long expression, is the worst case
and is exactly the input an attacker would supply.

Second, the traversal is depth first and pre-order or post-order depending on
whether the composite does its own work before or after recursing. Nothing about
the pattern forces a choice, and the choice is observable to anybody who relies
on ordering, so it belongs in the interface documentation rather than in the
reader's head.

Third, the operation is not atomic. If another thread mutates the child list of
a composite while a traversal is in progress, the traversal may see a partially
updated structure, skip a node, visit a node twice, or throw a concurrent
modification error halfway through. Dimension 11 covers the symptom.

Here is the same flow when the structure is not a tree. This diagram is the
failure, not the design, and it is drawn because the failure is common.

```
     Composite A                   A.children = [B]
     +-----------+                 B.children = [A]      <-- the cycle
     |     A     |----+
     +-----------+    |
           ^          v
           |    +-----------+
           +----|     B     |
                +-----------+

  A.size()
    -> B.size()
      -> A.size()
        -> B.size()
          -> A.size()
            ... no base case is ever reached ...

  Result: stack exhaustion. Java StackOverflowError, Python RecursionError,
  Go fatal "goroutine stack exceeds limit", C or C++ segmentation fault.
  Nothing in the Composite pattern prevents this. The guard is external.
```

## 8. Implementation variants

**Transparent child management (GoF recommended).** `add`, `remove` and
`getChild` are declared on Component. Every client can treat every node the same
way, including when building the structure, and a client that walks a tree
generically can descend without a type test. The cost is that a Leaf must supply
an implementation, and the honest implementation throws. The GoF book is explicit
that this trades safety for transparency and comes down on the side of
transparency ([Wikipedia summary of the two design variants](https://en.wikipedia.org/wiki/Composite_pattern),
verified 2026-08-02). The book also notes the choice splits by language
community, with Smalltalk implementations placing child management on Composite
and C++ implementations placing it on Component.

**Safe child management.** `add` and `remove` live only on Composite. The
compiler rejects `leaf.add(x)`, which converts a runtime exception into a
compile error. The cost is that any client that builds or mutates the structure
has to know it is holding a Composite, which means a cast, a type test, or a
separate builder API. Read-only clients are unaffected, which is the part people
miss when they argue about this.

**Recommendation, and the reason.** Prefer the safe form for a domain model you
own, and prefer the transparent form for a framework whose clients write generic
tree tooling. The reason is that the two forms fail differently and one failure
is much cheaper than the other. The safe form fails at compile time in the code
that builds the tree, which is normally a small, well tested part of the system,
and the fix is local. The transparent form fails at runtime in the code that
walks the tree, which is normally the largest and most widely reused part of the
system, and the fix requires knowing which node threw. A DOM implementation
chooses transparency because generic tooling is the point. A pricing engine
chooses safety because nothing generic walks its rules.

There is a middle position that is usually better than either, and it is the one
most modern APIs land on. Keep child management off Component, but add a
read-only `children()` accessor that returns an empty sequence for a leaf. Now
every reader is generic and needs no type test, no method throws, and only
writers need the concrete type. That is the arrangement Roslyn uses, where
`SyntaxNode` exposes `ChildNodes()` and `DescendantNodes()` on every node while
tree construction goes through separate factory and `With...` APIs
([Microsoft.CodeAnalysis.SyntaxNode](https://learn.microsoft.com/en-us/dotnet/api/microsoft.codeanalysis.syntaxnode),
verified 2026-08-02).

**Immutable composite with structural sharing.** Nodes are read only and every
edit returns a new root, reusing every unmodified subtree. Removes the
concurrency hazard from dimension 7 entirely, makes equality and caching cheap,
and makes undo free. Costs one allocation per node on the path from the edit to
the root, so an edit deep in a large tree allocates proportionally to depth
rather than to size, which is usually acceptable. This is the model Roslyn syntax
trees and React element trees both use.

**Explicit stack or queue traversal.** The composite operation is written as a
loop over an explicit stack rather than as recursion. Bounded by heap rather than
by the call stack, so it survives adversarial depth, and the largest frontier
size becomes observable and boundable. Costs readability, because the elegant
three-line recursive method becomes fifteen lines, and it loses the natural
post-order combination point unless a second pass or an accumulator is added.
Use a stack for depth first and a queue for breadth first, and note the breadth
first form has a different memory profile, proportional to the widest level
rather than to the height.

**Caching composite.** The composite stores the combined result and invalidates
on mutation, usually by propagating a dirty flag upward through parent
references. Turns repeated queries from linear to constant. The cost is that
correctness now depends on every mutation path setting the flag, and a single
missed invalidation produces a stale answer that no test written against a fresh
tree will catch. Only worth it when reads outnumber writes by a wide margin and
the invalidation surface is small.

**Parent back-reference.** Each Component holds a pointer to its parent. Enables
upward walks, ancestor queries, and detaching a node without knowing its owner,
which is what makes an `instanceof`-free tree editor possible. Roslyn exposes
this as `Parent` and builds `Ancestors()` on top of it. The costs are real. The
object graph now contains cycles, so naive deep copy and naive equality both
loop, reference-counted runtimes leak, and every mutation must update two places
instead of one.

**Flyweight leaves.** When leaves are numerous and immutable, share them rather
than allocating one per position. A syntax tree with ten thousand identifier
tokens does not need ten thousand distinct string objects. This turns the tree
into a directed acyclic graph, which is safe for traversal but breaks parent
back-references and breaks any code that assumes identity implies position.

**Type-parameterised composite.** In a language with generics, parameterise the
Component over the result type so one traversal skeleton serves many operations.
Reduces duplicated traversal code across operations at the cost of a more
demanding interface for implementors.

**Language note on Go and Rust.** Neither has implementation inheritance, so the
classical drawing does not translate directly. In Go the Component is an
interface and the Composite is a struct holding a slice of that interface, which
is arguably a cleaner expression of the pattern than the inheritance form,
because the shared interface is the only thing shared. In Rust the usual forms
are an enum with a recursive variant, which is the algebraic form and closes the
node set, or `Vec<Box<dyn Component>>`, which keeps the node set open at the cost
of dynamic dispatch and heap indirection. Choose the enum when node types are
fixed, since it enables exhaustive matching and removes allocation per node.

## 9. Known production uses

**The WHATWG DOM node tree.** The DOM Standard defines a tree as a finite
hierarchical structure in which each object has a parent and an ordered set of
children, and defines the `Node` interface with `childNodes`, `firstChild`,
`parentNode` and `appendChild` on every node type. Element nodes hold children,
text nodes do not, and both are `Node`, which is the transparent form of the
pattern applied at web scale. Section 1.1 covers trees and section 4.4 covers the
`Node` interface. WHATWG DOM Standard, https://dom.spec.whatwg.org/ verified
2026-08-02.

**`java.awt.Container` in the Java Abstract Window Toolkit.** The class
documentation states that a container object is a component that can contain
other AWT components, and the class declaration is `public class Container extends
Component`. That single line is the pattern. `add(Component comp)` appends a
child, and the ordering of the child list defines front-to-back stacking. Every
Swing container inherits this. Oracle, Java SE 21 API Specification,
`java.awt.Container`,
https://docs.oracle.com/en/java/javase/21/docs/api/java.desktop/java/awt/Container.html
verified 2026-08-02.

**Roslyn syntax trees, `Microsoft.CodeAnalysis.SyntaxNode`.** The class is
documented as representing a non-terminal node in the syntax tree, and it exposes
`ChildNodes()`, `DescendantNodes()`, `Ancestors()`, `Parent` and
`Contains(SyntaxNode)` on every node. This is a production compiler front end
whose entire public surface is a Composite, with the read-only accessor variant
described in dimension 8. Microsoft .NET API documentation,
`Microsoft.CodeAnalysis.SyntaxNode`,
https://learn.microsoft.com/en-us/dotnet/api/microsoft.codeanalysis.syntaxnode
verified 2026-08-02.

**Flutter widget trees, `MultiChildRenderObjectWidget`.** The class is documented
as a superclass for render object widgets that configure render objects with a
single list of children, and its `children` property is documented as the widgets
below this widget in the tree. A `Widget` describes the configuration for an
`Element`, and both single-child and multi-child widgets are `Widget`, so a
layout widget can hold layout widgets to arbitrary depth. Flutter API
documentation, `MultiChildRenderObjectWidget`,
https://api.flutter.dev/flutter/widgets/MultiChildRenderObjectWidget-class.html
and `Widget`, https://api.flutter.dev/flutter/widgets/Widget-class.html both
verified 2026-08-02.

**React component trees.** The React documentation states that a React
application begins at a root component, that most React apps use components all
the way down, and that a component rendering another component makes the first a
parent and the second a child. Components are uniform in the sense that a
component that renders one element and a component that renders a subtree are
both components and both usable anywhere a component is expected. React
documentation, "Your First Component",
https://react.dev/learn/your-first-component verified 2026-08-02.

**`java.nio.file.Files` tree walking, and its cycle guard.** `Files.walk` returns
a stream lazily populated by walking the file tree rooted at a starting file,
which is Composite traversal over the directory hierarchy. The relevant part for
this entry is that the Java standard library ships a dedicated exception,
`FileSystemLoopException`, documented as thrown when a file system loop, or
cycle, is encountered. A production tree walker over a structure that can contain
cycles needs explicit cycle detection, and the standard library says so by
shipping the exception. Oracle, Java SE 21 API Specification,
`java.nio.file.FileSystemLoopException`,
https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/nio/file/FileSystemLoopException.html
verified 2026-08-02.

## 10. Consequences

Positive.

- Client code contains no conditional logic over node kinds. One call at the root
  covers a structure of any shape, and the conditional that would otherwise
  appear in every client appears nowhere.
- New node types are added without editing any existing code, which is the Open
  Closed Principle applied to a data structure. A plugin can contribute a node
  type from a separate module.
- The recursion is written once, inside the Composite, rather than once per
  client. Bugs in the recursion have one home and one fix.
- Structures compose without limit, so a tree assembled by one subsystem can be
  handed to another as a single node with no adaptation.
- The uniform interface makes structural operations, copying, comparison,
  serialisation and printing, writable generically over the whole family.
- Testing becomes cheaper for clients, because a client can be exercised against
  a single leaf standing in for an arbitrarily large tree.

Negative.

- The shared interface tends to widen until it accommodates every node type, at
  which point it constrains nothing and the type system stops helping. This is
  the anti-pattern in dimension 11 and it is the most common way Composite goes
  wrong in a long-lived codebase.
- In the transparent form, type safety is lost for child management. Leaves carry
  methods that always fail, which is a documented lie in the type signature.
- Adding an operation touches every node type, so the cost of change is
  asymmetric and grows with the number of node types.
- Performance is not free. One dispatch per node, pointer chasing, and no
  opportunity for the contiguous memory access a flat representation would give.
- Recursive traversal is bounded by the call stack, so depth becomes an input
  validation concern rather than an implementation detail.
- Debugging is harder. A stack trace shows the same three frames repeated forty
  times and does not say which branch of the tree produced the failure.
- Constraints on which node types may contain which other node types cannot be
  expressed in the type system once everything is a Component. They become
  runtime checks or, more often, undocumented assumptions.

## 11. Failure modes and misuse

**Cycle in a structure assumed to be a tree.** Symptom. A stack overflow with a
trace of identical repeating frames, appearing in production on one tenant and
never reproducible locally. Cause. A composite was added to itself, directly or
through a chain, usually by a move or reparent operation that did not check
whether the destination sat inside the subtree being moved. Fix, and there are
three layers of it. Reject the cycle at insertion time by walking upward from the
destination and refusing if the node being inserted is an ancestor. This is
exactly what the DOM does, throwing `HierarchyRequestError` when the insertion
would create a cycle, that is when the child is an ancestor of the node
([MDN, `Node.appendChild()`](https://developer.mozilla.org/en-US/docs/Web/API/Node/appendChild),
verified 2026-08-02). Where the structure genuinely can contain cycles, as with
symbolic links in a file system, carry a visited set through the traversal and
fail loudly, which is what `FileSystemLoopException` exists for. As a backstop,
cap traversal depth so an undetected cycle produces a bounded error rather than a
crash.

**Everything becomes a Component.** Symptom. The Component interface has grown to
twenty methods, most node types implement four of them properly and throw or
return a default for the rest, and code review arguments about where a new method
belongs have no answer because every location is equally arbitrary. A newcomer
cannot say what a Component is without listing the subclasses. Cause. The
uniformity was treated as a goal rather than as a consequence of a real domain
property, so each new requirement was accommodated by widening the interface
rather than by questioning whether the requirement belonged in the hierarchy.
This is the Composite anti-pattern, and it is corrosive because it degrades
slowly and every individual step looks reasonable. Fix, in order. Split the
Component interface by capability, so a node type declares which capabilities it
has and clients query for the capability instead of assuming it. Move operations
that only apply to one node type off the interface entirely and reach them
through a narrower type. Where the hierarchy has absorbed two unrelated concepts,
separate them into two hierarchies even at the cost of duplicating a traversal.
The preventive rule is a hard one. A method belongs on Component only when every
node type has a real, non-throwing, non-default implementation of it, and when it
does not, the interface is the wrong home.

**Deep recursion on adversarial input.** Symptom. A crash rather than an error
response, on an endpoint that parses a nested document. A JSON body of ten
thousand open brackets, or an expression with ten thousand nested parentheses,
produces a stack overflow that is not catchable in a way that leaves the process
healthy. Cause. Recursive descent over a Composite with no depth limit. Fix.
Bound the depth at parse time and reject beyond it, before the structure exists,
and use the explicit stack form for any traversal that runs on untrusted input.
This is a denial of service vector, and dimension 17 returns to it.

**Silent failure on a leaf.** Symptom. A configuration change appears to succeed
and has no effect. Cause. The transparent form was implemented with `add` as a no
operation on Leaf rather than as a throw, on the reasoning that throwing was
unfriendly. The call succeeded, the child went nowhere, and nothing reported it.
Fix. Throw. An operation that cannot be honoured must say so. A no-op child
management method on a leaf converts a loud, findable bug into a quiet one.

**Concurrent modification during traversal.** Symptom. An intermittent
`ConcurrentModificationException`, or worse, a traversal that silently skips a
subtree under load and produces a total that is short by an amount nobody can
reproduce. Cause. A mutable Composite traversed while another thread edits it.
Fix. Make the structure immutable and treat edits as producing a new root, or
snapshot the child collection at the start of each composite operation, or take a
lock at the root for the duration of the traversal and accept the contention.

**Combinatorial blow-up through a shared subtree.** Symptom. A traversal that
should be linear takes minutes, and the node count reported by the traversal far
exceeds the number of distinct objects. Cause. The structure is a directed
acyclic graph rather than a tree, because a subtree was shared between several
parents, often deliberately as a memory optimisation. A traversal without
memoisation visits a shared node once per path that reaches it, which is
exponential in the worst case. Fix. Memoise on node identity when the operation
is pure, or copy on share so the structure really is a tree.

**Leaf pretending to be a composite for convenience.** Symptom. A node type that
returns a hard-coded single child from `getChild` and answers one to a child
count, and downstream code that mysteriously double counts. Cause. A leaf was
made to look composite so one client could avoid a special case. Fix. Give that
client the special case. One local conditional is cheaper than a node type that
lies about its shape.

**Order dependence that is not in the contract.** Symptom. A rendering or a total
changes after an unrelated refactor that swapped a list for a set. Cause. The
Composite's iteration order was load bearing but undocumented, so a change of
collection type changed behaviour. Fix. State the ordering guarantee on the
interface and pick a collection that provides it, or make the combination
commutative so the order genuinely cannot matter.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Composite | Decorator | Chain of Responsibility | Flat list plus a parent key | Algebraic sum type with pattern matching | Interpreter |
|---|---|---|---|---|---|---|
| Client sees one interface | Yes, that is the point | Yes, but for wrapping not nesting | Yes, but only for the request | No. Client reconstructs the shape | Yes, but the client matches on the case | Yes, over a grammar |
| Adding a node type | No edits anywhere | No edits, add a decorator | No edits, add a handler | No edits, add a row type | Edits every match site | No edits, add a rule |
| Adding an operation | Edits every node type | Edits every decorator | Edits the handler interface | One new function over the table | One new function, no type edits | Edits every rule |
| Arbitrary depth | Yes, unbounded | Yes, but linear not branching | Linear only, no branching | Yes, at query cost | Yes, unbounded | Yes, unbounded |
| Type safety of structure edits | Weak in transparent form, strong in safe form | Strong. Wrapping is always legal | Strong | Strong at the row level, weak at the shape level | Strong. Illegal shapes do not compile | Weak, same as Composite |
| Cycle safety | None. Must be added externally | Cycles are possible and equally fatal | Cycles are possible and equally fatal | Detectable with a query | Impossible if the type is inductive | None |
| Traversal latency | One dispatch per node, pointer chasing | One dispatch per layer | One dispatch per handler until handled | One scan, contiguous memory | One match per node, often inlinable | One dispatch per node |
| Stack depth risk | High for deep trees | Low. Depth is usually small | Low. Depth is usually small | None. Iterative by construction | High, same recursion | High |
| Cognitive load | Medium. Simple per node, hard to trace | Low | Low | Medium. Shape is implicit | Medium. Exhaustiveness helps | High |
| Persistence fit | Poor. Recursive queries or nested sets | Not applicable | Not applicable | Strong. That is its purpose | Poor, same as Composite | Poor |
| Best when | Domain is genuinely recursive, node set open | Behaviour is added in layers | One of many handlers should act | Structure is queried more than executed | Node set closed, operation set open | The tree is a program |

Reading of the table. Composite and the algebraic sum type describe the same
data and differ on which axis is cheap to extend. Composite is cheap in node
types and expensive in operations, the sum type is the reverse, and the choice
should follow whichever axis actually moves in the codebase. Decorator and Chain
of Responsibility are frequently confused with Composite because all three
produce a runtime object graph behind one interface, but both of those are linear
and neither branches, which is the whole difference. A flat table with a parent
key wins when the main requirement is querying the structure rather than running
behaviour over it.

## 13. Related and incompatible patterns

- **Decorator.** The closest structural relative and the most confused with it.
  Both put a wrapper behind the same interface as the thing wrapped. Decorator
  holds exactly one child and adds behaviour to it. Composite holds many children
  and aggregates over them. A Decorator with a list is a Composite, a Composite
  restricted to one child is a Decorator, and the two are routinely used together
  in graphics and middleware stacks where a decorated node sits inside a
  composite group. The GoF book presents them as sharing a recursive structure
  with different intents.
- **Visitor.** The standard partner, and the answer to the asymmetric cost of
  change from dimension 10. Visitor moves an operation out of the node types into
  a single class with one method per node type, so adding an operation touches
  one file rather than every node type. The composition is direct. Component
  declares `accept(visitor)`, each Leaf calls the matching visit method, and each
  Composite calls the matching visit method and recurses into its children,
  usually through a base walker that supplies the traversal so concrete visitors
  supply only the interesting cases. Roslyn ships exactly this shape, where
  `CSharpSyntaxWalker` is documented as a visitor that descends an entire syntax
  node graph, visiting each node and its children in depth-first order
  ([Microsoft .NET API documentation, `CSharpSyntaxWalker`](https://learn.microsoft.com/en-us/dotnet/api/microsoft.codeanalysis.csharp.csharpsyntaxwalker),
  verified 2026-08-02). The trade is explicit. Visitor makes operations cheap and
  node types expensive, because every new node type requires a new method on
  every visitor. Adopt it when the node set has stopped changing and the
  operation set has not. Adopting it early, while node types are still being
  added weekly, buys the wrong side of the trade.
- **Iterator.** The other standard partner, and the one that separates traversal
  from operation. A composite that exposes an iterator over its descendants lets
  clients write ordinary loops rather than recursive functions, which means a
  client can stop early, filter lazily, or process in a pipeline. The composition
  matters more than it appears, because the iterator is where the explicit stack
  from dimension 8 belongs. Writing the traversal once, iteratively, inside an
  iterator gives every client bounded stack usage for free without any client
  knowing. `Files.walk` returning a lazily populated stream over a directory tree
  is this composition in the Java standard library, and `SyntaxNode.DescendantNodes()`
  is the same composition in Roslyn. Where Visitor pushes the operation into the
  structure, Iterator pulls the structure out to the operation, and the two are
  alternatives more often than they are used together.
- **Builder.** Composes cleanly and solves a real problem the pattern creates.
  Assembling a deep tree by hand is verbose and, in the safe form, requires
  knowing concrete types. A builder with a fluent nesting API hides that, and
  keeps the concrete Composite type out of client code entirely.
- **Flyweight.** Composes with it to make large trees affordable, by sharing
  immutable leaves across many positions. The limitation is stated in dimension
  8. A shared leaf has no single parent, so parent back-references and
  identity-based position logic both stop working.
- **Interpreter.** A specialisation rather than a partner. An Interpreter is a
  Composite whose Component is a grammar rule and whose operation is `interpret`.
  Every consequence in this entry applies to it, including the stack depth risk,
  which is why real interpreters over untrusted input bound their recursion.
- **Chain of Responsibility.** Frequently confused, and the distinction is worth
  keeping sharp. A chain is linear and its point is that exactly one handler
  acts. A composite branches and its point is that every node acts. A chain built
  on parent back-references through a composite is a genuine and useful hybrid,
  used for event bubbling in the DOM, but it is a different pattern operating
  over the same structure.
- **Null Object.** A natural fit. An empty Composite is a Null Object for the
  whole family when the combination is a monoid, which removes null checks from
  every client at once.
- **Singleton.** Conflicts in practice. A Composite node held as a process-wide
  singleton cannot be placed in two trees, cannot be tested in isolation, and
  makes the identity assumptions in dimension 11 false. Scope nodes to the tree.

## 14. Refactoring path in and out

Introducing the pattern into code that does not have it. The named refactorings
are Replace Conditional with Polymorphism and Extract Superclass, and the
refactoring family entries cover both. Ordered steps.

1. Find the conditional that tests node kind. It is normally a type switch or an
   `instanceof` chain inside a loop, and it has normally been copied to two or
   three call sites. List every copy before changing anything, because the copies
   are the evidence that the pattern will pay.
2. Name the operation the conditional is computing and give it a signature that
   makes sense for both a single element and a group. If no such signature
   exists, stop. The pattern does not apply and dimension 4 explains why.
3. Extract the Component interface with that one operation. One operation only.
   Widening the interface at this stage is how the anti-pattern in dimension 11
   starts.
4. Make the existing element type implement Component. Run the tests. Nothing has
   changed behaviourally, and this step should be boring.
5. Create the Composite type holding a list of Component, and implement the
   operation by delegating and combining. Do not add child management to
   Component yet, and preferably never.
6. Replace the conditional at one call site with a call through Component. Run the
   tests. Repeat per call site, one at a time, so a failure localises to the site
   most recently changed.
7. Delete the conditional once the last call site is converted. If a call site
   resists conversion, that site needs something the Component interface does not
   express, and the answer is to look at that requirement rather than to widen
   the interface reflexively.
8. Add the cycle guard from dimension 11 before the structure is exposed to any
   input that a user controls. Introducing the pattern and adding the guard later
   means shipping the failure mode in between.
9. Only now consider whether child management belongs on Component, using the
   recommendation in dimension 8.

Removing the pattern when it stops earning its place. The signals are a Component
interface that has grown past what every node type can implement honestly, a tree
whose depth turns out to be bounded at two, or a traversal that has become the
largest cost in a profile.

1. Measure which node types actually occur and at what depth. If the answer is
   two levels, the recursion is speculative and step 2 applies. If the answer is
   deep but the cost is dispatch, step 5 applies instead.
2. For the bounded-depth case, replace the recursive Composite with an explicit
   two-level model, a group holding elements. Convert clients one at a time. This
   is Collapse Hierarchy, see the refactoring family entry.
3. For the widened-interface case, split Component by capability first rather
   than removing the pattern. Most of the pain is the interface, not the
   recursion, and splitting usually resolves it without giving up uniformity.
4. Where an operation was pushed onto Component only to satisfy one client, pull
   it back out to that client and give the client the type test it needs. One
   honest conditional beats a dishonest interface.
5. For the performance case, keep the Component interface as the public surface
   and replace the internal representation with a flat array plus index-based
   parent or child links, exposing an iterator over it. Clients do not change,
   and the pointer chasing goes away. This is Replace Data Structure and it is
   the least disruptive of the removals because the seam holds.
6. Delete the Composite type only when no client relies on passing a group where
   an element is expected. That property is the pattern, and once it is gone the
   remaining classes are a container and its contents.

## 15. Testing and verification

Easier because of the pattern.

- A client can be tested against a single leaf. Because a leaf and a hundred-node
  tree satisfy the same interface, most client tests need no tree at all, which
  removes a large amount of fixture construction.
- The combination rule is testable in isolation by building a composite over two
  stub leaves with known values, which turns the interesting half of the logic
  into a two-line test.
- A test double is trivial. A stub Component returning a fixed value needs no
  mocking framework, and a spy Component that records that it was visited gives
  traversal-order assertions cheaply.
- Structural invariants are checkable generically, because one recursive
  validator over Component covers every node type including ones added later.

Harder because of the pattern.

- Coverage over shapes is not the same as coverage over types. A suite that
  exercises every node type can still miss the empty composite, the single-child
  composite, the deep chain and the wide fan, and those four shapes are where the
  bugs are.
- A failure inside a deep traversal reports a leaf, not a path, so a failing test
  says what broke and not where. Including the path in the assertion message is
  worth the effort in any suite over a tree of real size.
- Performance regressions hide well. A change that adds one allocation per node
  is invisible on a ten-node fixture and measurable on a ten-thousand-node
  production tree.

Techniques that apply.

- **Shape-based test matrix.** Write one test per structural shape rather than
  per node type. The minimum set is the empty composite, a single leaf, a
  composite of leaves, a composite of composites, the deepest chain the system
  allows, and the widest fan it allows. This matrix catches the base-case and
  combination bugs that a type-based matrix walks past.
- **Property-based testing over generated trees.** Generate random trees and
  assert invariants that must hold for any shape. Useful properties include that
  the sum over a composite equals the sum over its flattened leaves, that
  traversal visits each node exactly once, and that an operation on a composite
  of one child equals the operation on that child. This is the technique that
  finds the shared-subtree double counting from dimension 11, because a generator
  will produce sharing that a handwritten fixture never does. See the
  property-first testing discipline in the testing family.
- **Depth-bound test.** One test that constructs a tree deeper than the expected
  production maximum and asserts a bounded error rather than a crash. This is the
  only test that catches the stack overflow before an attacker does, and it
  should be written the day the pattern is introduced.
- **Cycle-rejection test.** One test per mutation entry point asserting that
  inserting an ancestor into its own descendant is rejected. Entry points are
  easy to miss, so enumerate them from the type rather than from memory.
- **Contract test over Component.** One abstract test class written against the
  Component interface, subclassed once per node type. Every implementation,
  including ones contributed later by other teams, inherits the same suite. This
  is the technique that keeps an open node set honest.
- **Snapshot test on the rendered structure.** For trees whose output is textual
  or visual, a serialised snapshot of the whole tree catches structural
  regressions that per-node assertions miss.

## 16. Observability signals

The pattern hides shape from the source, so shape has to appear in telemetry or
nobody can diagnose a production failure in it.

What to record.

- On each traversal, one span at the root carrying node count, maximum depth and
  elapsed time. Per-node spans are almost always the wrong choice, because they
  multiply trace volume by the node count and cost more than they explain. One
  span with three attributes answers most questions.
- A histogram of tree depth at ingestion, labelled by source. Depth is the input
  that determines whether the stack risk is theoretical or imminent, and it is
  the earliest warning available.
- A histogram of node count per traversal, labelled by operation. A gap between
  the node count and the count of distinct node identities is the shared-subtree
  signal from dimension 11.
- A counter of cycle rejections at insertion, labelled by entry point. A non-zero
  value is either an attack or a bug in a caller, and both are worth knowing
  about. A value that is always zero across a fleet is weak evidence the guard is
  not wired up, which is worth a synthetic check.
- A counter of leaf child-management rejections, when the transparent form is in
  use. Every increment is a client that believes a leaf is a composite.
- For caching composites, a hit rate and an invalidation counter. A hit rate near
  one hundred percent with no invalidations usually means invalidation is broken
  rather than that the cache is perfect.
- The path from root to the failing node on every error raised inside a
  traversal. This is the single most useful field, and it costs an accumulator
  threaded through the recursion.

A healthy instance on a dashboard. Depth is stable and well inside the configured
bound, with a distribution whose tail moves only when a known input source
changes. Node count per traversal tracks the size of the underlying data rather
than growing on its own. Traversal duration is close to linear in node count,
which shows on a scatter of duration against node count as a straight line
through the origin. Cycle rejections are zero or near zero and attributable.

A failing instance. Depth develops a long tail with no matching change in data
volume, which is the shape of an adversarial input or of a reparent bug slowly
building a chain. Duration grows super-linearly against node count, which is the
shared-subtree blow-up. Node count climbs while distinct identity count stays
flat, same cause seen from the other side. Cycle rejections spike from one source
address, which is an attack rather than a bug. Traversal errors cluster on one
path prefix, which localises a corrupt subtree without reading any code. Leaf
rejection counters climb after a deploy, which points at a client that started
treating a leaf as a container.

## 17. Security and privacy implications

The pattern is not neutral on security, and pretending otherwise would misstate
it. Recursion over attacker-influenced structure is a real attack surface and it
has three distinct forms.

**Stack exhaustion through depth.** A parser that builds a Composite from
untrusted input, then traverses it recursively, gives an attacker direct control
over call stack depth. A payload of deeply nested brackets, elements or
parentheses costs the attacker bytes and costs the server a crash. This is not
theoretical. It is the standard shape of nesting-depth denial of service against
document parsers. The defences layer. Bound nesting depth during parsing and
reject beyond it, before the structure exists, so the cost is paid at the
cheapest possible point. Use the explicit stack traversal from dimension 8 on any
path reachable from untrusted input, so the bound is heap rather than stack. Cap
total node count as well as depth, because a wide shallow tree exhausts memory
without exhausting the stack.

**Amplification through shared subtrees.** When a format permits a node to
reference another node, an attacker can construct a small document whose expanded
traversal is exponential. This is the billion-laughs class of attack, expressed
in Composite terms. A naive traversal that follows every reference every time
turns kilobytes of input into gigabytes of work. Defences are to memoise on node
identity, to cap the expanded node count rather than the input size, and to
refuse to resolve references at all where the use case does not need them.

**Cycles as a liveness attack.** An insertion path with no ancestor check lets a
caller build a cycle, after which any traversal hangs or crashes. Where the
insertion path is reachable from a user, this is a denial of service with a
one-request payload. The DOM's `HierarchyRequestError` on inserting an ancestor
is the reference behaviour to copy, and the file system case shows the other half
of the answer, where cycles cannot be prevented at insertion and so must be
detected during traversal with a visited set.

Two further implications are worth naming because they are less obvious.

**Authorisation does not compose automatically.** When a Composite operation
aggregates over children, the natural implementation checks permission at the
root and then trusts the recursion. If different subtrees carry different
sensitivity, that produces a confused deputy, where a caller authorised for a
parent reads a child it should not. The correct shape is to apply the check per
node during traversal and to filter rather than to fail, so an unauthorised
subtree contributes nothing rather than aborting the whole operation. Filtering
also leaks less, because failing loudly on an unauthorised subtree confirms that
the subtree exists.

**Aggregates can leak what individual nodes protect.** A total computed over a
tree can disclose information about nodes the caller cannot read individually. A
department headcount that includes a subtree the caller has no access to is a
small inference channel, and repeated queries against changing structure widen
it. Where the aggregate is sensitive, compute it over the caller's authorised
view rather than over the full structure.

On privacy the pattern is close to silent in itself, with one practical caveat
that follows from dimension 16. The advice there is to record the path from root
to node on error. A path is often a business identifier, a folder name, a
customer segment or a document title, so treat that field as attributable data
and apply the same retention, redaction and access rules as any other identifier
rather than treating it as a debug string.

## 18. References

1. Erich Gamma, Richard Helm, Ralph Johnson, John Vlissides. *Design Patterns.
   Elements of Reusable Object-Oriented Software*. Addison-Wesley, 1994.
   ISBN 0-201-63361-2. Chapter 4, Structural Patterns, section Composite,
   beginning at page 163. Source of the intent, the four participants, the
   transparency against safety discussion, and the note that the choice splits by
   language community.
2. Wikipedia contributors. "Composite pattern".
   https://en.wikipedia.org/wiki/Composite_pattern
   Verified 2026-08-02. Used to confirm the wording of the GoF intent, the
   participant list, and the two child-management design variants. Not used as a
   source of explanation.
3. WHATWG. *DOM Standard (Living Standard)*. Section 1.1 Trees, section 4.4
   Interface Node. https://dom.spec.whatwg.org/
   Verified 2026-08-02. Source for the node tree production use and for the
   parent and children definitions.
4. Mozilla. *MDN Web Docs*, `Node.appendChild()`.
   https://developer.mozilla.org/en-US/docs/Web/API/Node/appendChild
   Verified 2026-08-02. Source for `HierarchyRequestError` being thrown when the
   insertion would lead to a cycle, and for the move-not-copy semantics.
5. Oracle. *Java SE 21 API Specification*, `java.awt.Container`.
   https://docs.oracle.com/en/java/javase/21/docs/api/java.desktop/java/awt/Container.html
   Verified 2026-08-02. Source for the AWT production use, the
   `Container extends Component` declaration, and the ordered child list.
6. Oracle. *Java SE 21 API Specification*, `java.nio.file.FileSystemLoopException`.
   https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/nio/file/FileSystemLoopException.html
   Verified 2026-08-02. Source for cycle detection being a named condition in a
   production tree walker.
7. Microsoft. *.NET API documentation*, `Microsoft.CodeAnalysis.SyntaxNode`.
   https://learn.microsoft.com/en-us/dotnet/api/microsoft.codeanalysis.syntaxnode
   Verified 2026-08-02. Source for the Roslyn production use, the non-terminal
   node description, and the `ChildNodes`, `DescendantNodes`, `Ancestors` and
   `Parent` members.
8. Microsoft. *.NET API documentation*,
   `Microsoft.CodeAnalysis.CSharp.CSharpSyntaxWalker`.
   https://learn.microsoft.com/en-us/dotnet/api/microsoft.codeanalysis.csharp.csharpsyntaxwalker
   Verified 2026-08-02. Source for the Composite plus Visitor composition and the
   depth-first descent description.
9. Google. *Flutter API documentation*, `MultiChildRenderObjectWidget`.
   https://api.flutter.dev/flutter/widgets/MultiChildRenderObjectWidget-class.html
   Verified 2026-08-02. Source for the widget tree production use and the
   `children` property.
10. Google. *Flutter API documentation*, `Widget`.
    https://api.flutter.dev/flutter/widgets/Widget-class.html
    Verified 2026-08-02. Source for a widget describing the configuration for an
    element.
11. Meta. *React documentation*, "Your First Component".
    https://react.dev/learn/your-first-component
    Verified 2026-08-02. Source for the root component, the parent and child
    relationship, and components all the way down.

## Code examples

Four languages chosen because each shows a different genuine shape. TypeScript
shows both the transparent and safe forms side by side, which is the trade-off
this entry cares most about. Java shows the composition with Visitor. Python
shows the safe form plus an iterative traversal with a cycle guard, which is the
production-hardened version. Go shows the interface-plus-struct form that appears
where there is no implementation inheritance, together with an explicit stack
traversal. Rust is omitted from the runnable set because the idiomatic answer
there is a recursive enum, which is the algebraic form discussed in dimensions 1
and 12 rather than the object-oriented pattern.

### TypeScript

The transparent form. Child management sits on the shared interface, so a leaf
must reject it at runtime.

```typescript
interface Node {
  size(): number;
  add(child: Node): void;
  remove(child: Node): void;
}

class FileNode implements Node {
  constructor(private readonly bytes: number) {}
  size(): number {
    return this.bytes;
  }
  add(_child: Node): void {
    throw new Error("a file cannot contain children");
  }
  remove(_child: Node): void {
    throw new Error("a file cannot contain children");
  }
}

class DirNode implements Node {
  private readonly children: Node[] = [];
  size(): number {
    return this.children.reduce((total, c) => total + c.size(), 0);
  }
  add(child: Node): void {
    this.children.push(child);
  }
  remove(child: Node): void {
    const i = this.children.indexOf(child);
    if (i >= 0) this.children.splice(i, 1);
  }
}

const rootT = new DirNode();
rootT.add(new FileNode(1));
const srcT = new DirNode();
srcT.add(new FileNode(4));
rootT.add(srcT);
console.log(rootT.size());
```

The safe form. Child management is off the shared interface, so `leaf.add(x)`
does not compile and a writer must hold the concrete type.

```typescript
interface SafeNode {
  size(): number;
  children(): readonly SafeNode[];
}

class SafeFile implements SafeNode {
  constructor(private readonly bytes: number) {}
  size(): number {
    return this.bytes;
  }
  children(): readonly SafeNode[] {
    return [];
  }
}

class SafeDir implements SafeNode {
  private readonly kids: SafeNode[] = [];
  add(child: SafeNode): this {
    this.kids.push(child);
    return this;
  }
  size(): number {
    return this.kids.reduce((total, c) => total + c.size(), 0);
  }
  children(): readonly SafeNode[] {
    return this.kids;
  }
}

const rootS = new SafeDir().add(new SafeFile(1)).add(new SafeDir().add(new SafeFile(4)));
console.log(rootS.size());
```

### Java

The safe form plus a Visitor, which is the composition described in dimension 13.
Adding `NameVisitor` touches no node class, which is the trade Visitor buys.

```java
import java.util.ArrayList;
import java.util.List;

interface Node {
    <R> R accept(Visitor<R> v);
}

interface Visitor<R> {
    R visitFile(FileNode n);
    R visitDir(DirNode n);
}

final class FileNode implements Node {
    final String name;
    final long bytes;
    FileNode(String name, long bytes) {
        this.name = name;
        this.bytes = bytes;
    }
    public <R> R accept(Visitor<R> v) {
        return v.visitFile(this);
    }
}

final class DirNode implements Node {
    final String name;
    private final List<Node> children = new ArrayList<>();
    DirNode(String name) {
        this.name = name;
    }
    DirNode add(Node child) {
        children.add(child);
        return this;
    }
    List<Node> children() {
        return List.copyOf(children);
    }
    public <R> R accept(Visitor<R> v) {
        return v.visitDir(this);
    }
}

final class SizeVisitor implements Visitor<Long> {
    public Long visitFile(FileNode n) {
        return n.bytes;
    }
    public Long visitDir(DirNode n) {
        long total = 0;
        for (Node c : n.children()) {
            total += c.accept(this);
        }
        return total;
    }
}

final class NameVisitor implements Visitor<String> {
    public String visitFile(FileNode n) {
        return n.name;
    }
    public String visitDir(DirNode n) {
        StringBuilder sb = new StringBuilder(n.name).append("(");
        for (Node c : n.children()) {
            sb.append(c.accept(this)).append(" ");
        }
        return sb.append(")").toString();
    }
}

public final class Demo {
    public static void main(String[] args) {
        Node root = new DirNode("project")
                .add(new FileNode("README.md", 1))
                .add(new DirNode("src")
                        .add(new FileNode("main.java", 4))
                        .add(new DirNode("util").add(new FileNode("s.java", 12))))
                .add(new FileNode("LICENSE", 3));
        System.out.println(root.accept(new SizeVisitor()));
        System.out.println(root.accept(new NameVisitor()));
    }
}
```

### Python

The safe form, with a recursive size and an iterative walk that carries a visited
set. The iterative version is the one to reach for on untrusted input, because it
is bounded by the heap and it detects the cycle from dimension 11 rather than
crashing on it.

```python
from __future__ import annotations
from abc import ABC, abstractmethod
from collections.abc import Iterator, Sequence


class Node(ABC):
    @abstractmethod
    def size(self) -> int: ...

    def children(self) -> Sequence[Node]:
        return ()


class FileNode(Node):
    def __init__(self, name: str, size: int) -> None:
        self.name = name
        self._size = size

    def size(self) -> int:
        return self._size


class DirNode(Node):
    def __init__(self, name: str) -> None:
        self.name = name
        self._children: list[Node] = []

    def add(self, child: Node) -> DirNode:
        if self._creates_cycle(child):
            raise ValueError("insertion would create a cycle")
        self._children.append(child)
        return self

    def _creates_cycle(self, child: Node) -> bool:
        return any(n is self for n in walk(child))

    def children(self) -> Sequence[Node]:
        return tuple(self._children)

    def size(self) -> int:
        return sum(c.size() for c in self._children)


def walk(root: Node, max_nodes: int = 1_000_000) -> Iterator[Node]:
    # Explicit stack. Bounded by heap, not by the interpreter recursion limit.
    stack: list[Node] = [root]
    seen: set[int] = set()
    count = 0
    while stack:
        node = stack.pop()
        if id(node) in seen:
            continue
        seen.add(id(node))
        count += 1
        if count > max_nodes:
            raise RuntimeError("node budget exceeded")
        yield node
        stack.extend(reversed(node.children()))


def size_iterative(root: Node) -> int:
    return sum(n.size() for n in walk(root) if not n.children())


if __name__ == "__main__":
    util = DirNode("util").add(FileNode("s.py", 12))
    src = DirNode("src").add(FileNode("main.py", 4)).add(util)
    root = DirNode("project").add(FileNode("README.md", 1)).add(src).add(FileNode("LICENSE", 3))
    print(root.size())
    print(size_iterative(root))
    try:
        util.add(root)
    except ValueError as exc:
        print("rejected:", exc)
```

### Go

No implementation inheritance, so the Component is an interface and the Composite
is a struct holding a slice of that interface. The traversal is iterative with a
depth cap, which is the shape to prefer on any server path.

```go
package main

import (
	"errors"
	"fmt"
)

type Node interface {
	Size() int
	Children() []Node
}

type File struct {
	Name  string
	Bytes int
}

func (f *File) Size() int        { return f.Bytes }
func (f *File) Children() []Node { return nil }

type Dir struct {
	Name string
	kids []Node
}

func (d *Dir) Children() []Node { return d.kids }

func (d *Dir) Add(child Node) error {
	if contains(child, d) {
		return errors.New("insertion would create a cycle")
	}
	d.kids = append(d.kids, child)
	return nil
}

func (d *Dir) Size() int {
	total := 0
	for _, c := range d.kids {
		total += c.Size()
	}
	return total
}

func contains(root, target Node) bool {
	for _, n := range Walk(root, 1000) {
		if n == target {
			return true
		}
	}
	return false
}

type frame struct {
	node  Node
	depth int
}

// Explicit stack traversal. Bounded by maxDepth, not by the goroutine stack.
func Walk(root Node, maxDepth int) []Node {
	out := []Node{}
	seen := map[Node]bool{}
	stack := []frame{{root, 0}}
	for len(stack) > 0 {
		f := stack[len(stack)-1]
		stack = stack[:len(stack)-1]
		if f.depth > maxDepth || seen[f.node] {
			continue
		}
		seen[f.node] = true
		out = append(out, f.node)
		for _, c := range f.node.Children() {
			stack = append(stack, frame{c, f.depth + 1})
		}
	}
	return out
}

func main() {
	util := &Dir{Name: "util"}
	_ = util.Add(&File{"s.go", 12})
	src := &Dir{Name: "src"}
	_ = src.Add(&File{"main.go", 4})
	_ = src.Add(util)
	root := &Dir{Name: "project"}
	_ = root.Add(&File{"README.md", 1})
	_ = root.Add(src)
	_ = root.Add(&File{"LICENSE", 3})

	fmt.Println(root.Size())
	fmt.Println(len(Walk(root, 100)))
	fmt.Println(util.Add(root))
}
```
