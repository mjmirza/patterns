---
name: Visitor
slug: visitor
family: 01-design-patterns-gof
category: Behavioral
aliases: [Double Dispatch, Walker, Extrinsic Visitor]
first_described: "Gamma, Helm, Johnson, Vlissides 1994"
maturity: canonical
related: [composite, interpreter, iterator, strategy, template-method, command]
incompatible_with: [service-locator]
verified: 2026-08-02
---

# Visitor

## 1. Name, aliases, and lineage

The canonical name is Visitor. It is one of the eleven behavioral patterns in the
Gang of Four catalog, described in Erich Gamma, Richard Helm, Ralph Johnson and
John Vlissides, *Design Patterns. Elements of Reusable Object-Oriented Software*,
Addison-Wesley, 1994, chapter 5 (Behavioral Patterns), section Visitor. Robert C.
Martin's *Acyclic Visitor* paper records the Visitor section as beginning on page
331 of the 1995 Addison-Wesley printing, footnote 2
(https://condor.depaul.edu/dmumaugh/OOT/Design-Principles/acv.pdf, verified
2026-08-02).

The stated purpose is to represent an operation to be performed on the elements
of an object structure, so that a new operation can be defined without changing
the classes of the elements it operates on.

Names in real use, and what each one actually points at.

- **Double Dispatch.** Strictly the *mechanism*, not the pattern. Visitor is the
  best known way to build double dispatch in a single-dispatch language, and the
  two names get used for each other constantly. The mechanism predates the
  catalog. Daniel H. H. Ingalls described it for Smalltalk-80 in "A Simple
  Technique for Handling Multiple Polymorphism", OOPSLA '86 Proceedings,
  September 1986, page 347
  (https://algoritmos-iii.github.io/assets/bibliografia/simple-technique-for-handling-multiple-polymorphism.pdf,
  verified 2026-08-02). Ingalls opens with the observation that certain
  expressions are multiply polymorphic, meaning several terms in the expression
  may each be of variable type, and that conventional practice breaks down there,
  producing code that is not properly modular. That sentence describes the
  problem Visitor exists to solve, eight years before the catalog named it.
- **Walker.** Used in tree and syntax-tree libraries where the visitor also owns
  traversal rather than being driven by the elements. Roslyn ships
  `CSharpSyntaxWalker` under exactly this reading, documented as a
  `CSharpSyntaxVisitor` that descends an entire syntax node graph in depth-first
  order (https://learn.microsoft.com/en-us/dotnet/api/microsoft.codeanalysis.csharp.csharpsyntaxwalker,
  verified 2026-08-02).
- **Acyclic Visitor.** A distinct variant with its own paper, not a synonym. See
  dimension 8 and Robert C. Martin's paper cited above.
- **Extrinsic Visitor.** A name used for the reflective or type-test variant,
  where the element carries no `accept` method and the visitor does its own
  dispatch. It gives up static exhaustiveness in exchange for leaving the element
  hierarchy untouched.

There is one persistent confusion worth stating plainly. A class named `Visitor`
that receives a callback per node from a traversal function is not always the
Visitor pattern. If the traversal calls a single method and the method branches
on a runtime type test, the double dispatch is absent and the design is a
callback with a type switch inside it. The pattern proper requires that the
element itself select the visitor method, which is what the next dimension
explains.

## 2. Problem and context

There is a data structure whose shape is stable and whose set of node types
almost never changes, and there is a growing pile of operations over it, each of
which needs to do something different for each node type.

The situation reads like this in a codebase. There is an abstract syntax tree, a
document object model, a scene graph, a rule expression tree, an invoice line
hierarchy, or a file system tree. Twenty node types exist and have existed for
two years. Then someone needs a pretty-printer. Then a type checker. Then a cost
estimator. Then a validator. Then a serialiser. Then an optimiser.

The obvious first move is to add a method to the node interface for each new
operation. `print()`, `typeCheck()`, `estimateCost()`, `validate()`. That works
for two operations and rots at six. Every node class accumulates methods that
have nothing to do with each other, imports pull the printing library and the
cost model and the validation framework into the same file, and the node classes
stop being a data model and become a junk drawer. Adding an operation means
editing every one of the twenty node classes, which is a large diff touching
files owned by several teams, and the twenty edits are the same shape twenty
times.

The second obvious move is a free function that takes the node and switches on
its runtime type. `if (n instanceof Add) ... else if (n instanceof Mul) ...`.
That keeps the node classes clean, and it is genuinely the right answer in some
languages, see dimension 8. In a language without exhaustiveness checking it has
one bad property. When a twenty-first node type arrives, nothing tells you which
of the six operations forgot to handle it. The compiler is silent, the chain
falls through to the final `else`, and the failure appears at runtime in
production on the one input that contains the new node.

Visitor is the third move. It takes the operation out of the node classes, like
the type switch does, and it makes the compiler tell you about every missing case
when a node type is added, like the method-per-node approach does. It buys both
by paying a price the next dimensions describe.

The context that makes Visitor the right answer has three parts, and all three
must hold.

- The set of element types is closed in practice. New element types are rare
  events, measured in years, and are expected to be disruptive when they happen.
- The set of operations is open and growing. New operations are routine, measured
  in weeks, and are expected to be cheap.
- Operations are genuinely type-dependent. Each one needs a different body per
  element type, not the same body with a different parameter.

Outside that context Visitor is one of the most costly patterns in the catalog,
which is why dimension 4 carries an unusually long non-applicability list.

## 3. Forces

This dimension is engineering judgement about which pressure carries the most
weight, informed by the mechanism rather than measured from a benchmark.

- **Cost of adding an operation.** Strongly favoured. A new operation is one new
  class implementing one interface. No existing file is edited. This is the whole
  reason the pattern exists.
- **Cost of adding an element type.** Strongly sacrificed. A new element type
  forces a new method on the visitor interface, which breaks every visitor
  implementation everywhere, including implementations in other repositories. On
  a published interface this is a breaking change in the semantic-versioning
  sense.
- **Coupling.** Traded rather than reduced. The element hierarchy stops depending
  on the operations, which is the win. In exchange the element base type acquires
  a hard dependency on the visitor base type, and the visitor base type acquires
  a hard dependency on every concrete element type. Martin's paper names the
  result precisely, a cycle in the source-code dependency structure that makes
  `Element` transitively depend on all of its own derivatives.
- **Cognitive load.** Sacrificed heavily on first read. A reader tracing a call
  goes from `accept` on the element to `visitAdd` on the visitor, two hops, with
  no source line naming the destination. Readers new to the pattern reliably
  misread `accept` as doing nothing.
- **Cohesion of an operation.** Strongly favoured, and this is underrated. All
  twenty cases of the pretty-printer sit in one file, next to each other, sharing
  private helpers and accumulated state. In the method-per-node design those
  twenty cases are scattered across twenty files and cannot share a private
  helper without inventing a home for it.
- **Consistency and exhaustiveness.** Favoured. Because the visitor interface
  names every element type, a compiler in a statically typed language refuses to
  build a visitor that forgot one. That is a guarantee the type-switch design
  cannot offer without an exhaustiveness-checking language feature.
- **Latency.** Mildly sacrificed. Two virtual calls per node instead of one, plus
  the megamorphic call site problem described in dimension 11. Irrelevant on a
  hundred nodes, measurable on a hundred million.
- **Operability.** Sacrificed. Stack traces get deeper and less informative,
  because the frames read `accept`, `visitX`, `accept`, `visitY` and the actual
  traversal position is spread across the stack rather than held in a loop
  variable.
- **Team topology.** Favoured where a platform team owns the element hierarchy
  and many product teams own operations. Each product team ships a visitor in its
  own module without touching shared code. It becomes hostile the moment the
  platform team needs to add an element type, because that release breaks every
  downstream team at once.
- **Testability.** Favoured. An operation is a plain object with no dependency on
  the rest of the system, constructible in a test with two lines.

The summary of the trade is one sentence. Visitor moves the cost of change from
the operation axis to the element axis, and it is worth it only when change is
much more frequent on the operation axis.

### The expression problem, which is why the trade exists at all

The asymmetry above is not an implementation detail of Visitor. It is a general
result about type systems, and knowing it is what turns the choice of Visitor
from taste into engineering.

Philip Wadler named it in an email to the Java Genericity mailing list on 12
November 1998, stating the goal as defining a datatype by cases, where one can
add new cases to the datatype and new functions over the datatype, without
recompiling existing code, and while retaining static type safety
(https://homepages.inf.ed.ac.uk/wadler/papers/expression/expression.txt,
verified 2026-08-02). Wadler is explicit in the same message that this is a new
name for an old problem, and cites earlier discussion by Reynolds in 1975, Cook
in 1990, and Krishnamurthi, Felleisen and Friedman in 1998.

The shape of the problem is a two-dimensional grid. Rows are data variants, the
element types. Columns are operations. Every cell is one body of code. The
question is which direction you can extend without editing existing code.

```
                 print   evaluate   typeCheck   <- operations (columns)
    Literal        .         .           .
    Add            .         .           .
    Neg            .         .           .
      ^
      data variants (rows)

  Object-oriented method-per-node layout
      one CLASS per row. adding a ROW is free, adding a COLUMN
      edits every existing class.

  Functional type-switch layout
      one FUNCTION per column. adding a COLUMN is free, adding a ROW
      edits every existing function.

  Visitor
      chooses the FUNCTIONAL orientation inside an object-oriented
      language. one class per COLUMN. adding a column is free.
      adding a row breaks the Visitor interface and every implementor.
```

That is the whole reason Visitor is either perfect or terrible for a given
codebase, with almost nothing in between. It does not reduce the cost of change.
It rotates the grid. If your change traffic runs down the columns, the rotation
is a large win and every extra class is worth it. If your change traffic runs
across the rows, the rotation converts your cheapest change into your most
expensive one, and every extra class is dead weight on top.

So the first question when someone proposes Visitor is not whether the code is
tree-shaped. It is which axis has moved in the last year, and which axis the
planned work moves next. Answer that and the decision makes itself.

Two further notes keep the picture honest. First, no arrangement solves both
directions in a conventional single-dispatch object-oriented language without
giving something up, which is exactly why Wadler posed it as a problem rather
than an oversight. Second, the modern language features in dimension 8 do not
solve the expression problem either. Sealed hierarchies with pattern matching
pick the same orientation Visitor picks, favouring operations over variants. They
win because they deliver that orientation with a fraction of the machinery, not
because they escaped the trade.

## 4. Applicability and non-applicability

Reach for Visitor when the following hold together.

- An object structure has many distinct element types, and many unrelated
  operations must be performed over it.
- The element types are closed in practice, and adding one is understood to be a
  breaking, coordinated event.
- The operations do not belong in the element classes, because they encode
  concerns the element classes should not know about, such as rendering,
  persistence formats, cost models, or target machine code.
- You want the compiler to fail the build when a new element type arrives and an
  operation has not been updated, rather than finding out at runtime.
- Operation state must accumulate across a traversal, such as a symbol table, an
  indentation depth, or a running total. The visitor object is the natural home
  for that state, and a set of free functions is not.
- The operations must be shipped by code the element hierarchy's author does not
  control, in a separate module or a separate repository.

Do NOT reach for Visitor in these cases. The non-applicability list is the more
useful of the two, and the reason for each entry matters more than the entry.

- **The element hierarchy is still changing.** This is the single most common
  misuse. If new element types arrive monthly, every arrival breaks every
  visitor, and the pattern converts a cheap change into an expensive one across
  the whole system. Martin's paper states the condition in the reverse
  direction, recommending Acyclic Visitor over Visitor specifically when the
  visited class hierarchy will be frequently extended with new derivatives of the
  element class.
- **The language has sealed hierarchies plus exhaustive pattern matching.** In
  Java 21 and later, Kotlin, Rust, Swift, Scala, C# with recent switch
  expressions, and TypeScript with discriminated unions, the language feature
  gives you the same compile-time exhaustiveness with none of the classes and
  none of the double dispatch. See dimension 8, which states plainly where the
  language retires the pattern.
- **There are only two or three element types.** The visitor interface, the
  `accept` methods and the concrete visitor classes cost more code than the type
  switch they replace. A three-arm `switch` is readable at a glance and a
  three-method visitor interface is not.
- **There is only one operation, or the operations are not type-dependent.** If
  every element does the same thing with a different field, that is a method on
  the element interface, or a data-driven table. Visitor with one implementation
  is speculative structure.
- **The operation needs private state of the element.** Visitor forces the
  element to expose everything the operation needs, which widens the public
  surface of every element class and can leak representation. If the operation
  needs internals, it belongs on the element, and pushing it out with Visitor
  trades encapsulation for extensibility. The GoF catalog names this consequence
  directly, that Visitor can break encapsulation.
- **The traversal order is the interesting part, not the per-node work.** That is
  Iterator, or a plain recursive walk with a callback. Visitor addresses which
  code runs for which type, not the order in which nodes are reached.
- **You need to dispatch on two runtime types that are both open.** Visitor
  handles double dispatch only when one of the two hierarchies is closed. If both
  the element set and the operation set are open, no single-dispatch arrangement
  works, and the honest answers are multimethods, a registered pair table, or a
  redesign.
- **The structure is a small, flat, homogeneous collection.** Visiting a list of
  identical records is a `for` loop with a function, and dressing it as a Visitor
  adds a vocabulary the reader must learn for no gain.
- **The elements are data transfer objects you do not own.** You cannot add
  `accept` to a type from a third-party library. The reflective or type-test
  variant is the only option there, and at that point you have given up the
  compile-time guarantee that motivated the pattern.

## 5. Structure

Five participants, named by the role each one plays.

- **Element.** The abstract type of the things being visited. Its one obligation
  is to declare the `accept` operation taking a Visitor. It declares nothing
  about any specific operation.
- **ConcreteElement.** A node type. It implements `accept` with a body that is
  identical in every concrete element except for the method it calls, namely
  `visitor.visitThisType(this)`. That single line is where double dispatch
  happens, and it must be written in each concrete element rather than inherited,
  because the type of `this` at that line is what selects the visitor method.
- **Visitor.** The abstract type of the operations. It declares one visit
  operation per ConcreteElement, overloaded on the element type or named
  distinctly. This interface is the compile-time record of the closed element set,
  and it is what breaks when the set changes.
- **ConcreteVisitor.** One operation. It implements every visit method and
  usually carries mutable state accumulated over the traversal, such as an output
  buffer, a scope stack, or an error list. Each ConcreteVisitor is a coherent unit
  and can be read start to finish without opening any element class.
- **ObjectStructure.** The thing that holds elements and hands them to the
  visitor. It may be a collection, a Composite tree, or the root node itself. It
  owns the traversal policy, or it delegates traversal into the elements, which is
  a real design fork covered in dimension 8.

Relationships. Element depends on Visitor, because `accept` names it. Visitor
depends on every ConcreteElement, because each visit method names one.
ConcreteElement inherits Element. ConcreteVisitor inherits Visitor. The client
holds an ObjectStructure and a ConcreteVisitor and joins them.

The resulting dependency shape is the cycle Martin's paper is written about, and
it is worth naming precisely because it is the pattern's structural cost.
Element depends on Visitor, Visitor depends on ConcreteElement, and
ConcreteElement depends on Element. Element therefore transitively depends on
every one of its own subclasses. In a language with header-based compilation that
means every new element type triggers a rebuild of everything that touches the
element base type. Martin notes the mitigation, forward declarations reduce this
to what Lakos calls a name-only dependency, but the cycle survives and every
existing derivative of Element must still be recompiled when a new one appears.

## 6. ASCII structure diagram

```
   +---------------------+   accept(v)  calls   +----------------------+
   |      Element        |- - - - - - - - - - ->|       Visitor        |
   |---------------------|                      |----------------------|
   | + accept(v: Visitor)|                      | + visitLiteral(Lit)  |
   +---------------------+                      | + visitAdd(Add)      |
             ^                                  | + visitNeg(Neg)      |
             |                                  +----------------------+
     +-------+--------+--------------+                     ^
     |                |              |                     |
+----------+   +-----------+   +-----------+     +---------+---------+
| Literal  |   |   Add     |   |   Neg     |     |                   |
|----------|   |-----------|   |-----------|  +-----------+  +--------------+
| accept() |   | accept()  |   | accept()  |  | Printer   |  | Evaluator    |
+----------+   +-----------+   +-----------+  |-----------|  |--------------|
     ^              ^               ^         | visitLit  |  | visitLit     |
     |              |               |         | visitAdd  |  | visitAdd     |
     +--------------+---------------+         | visitNeg  |  | visitNeg     |
        Visitor names every one of these      +-----------+  +--------------+
        the cycle is Element -> Visitor -> ConcreteElement -> Element

   +---------------------+
   |   ObjectStructure   |  holds Elements, hands each to a Visitor
   +---------------------+
```

## 7. Dynamics

The runtime property that defines the pattern is that neither call alone knows
both types, and the two calls together do. The client knows the operation but not
the node type. The `accept` call resolves the node type but not the operation.
The `visit` call resolves the operation now that the node type is fixed by which
`accept` body is running.

```
Client            Add(node)          Printer(visitor)        Literal(child)
  |                   |                     |                     |
  |-- accept(printer) ->                    |                     |
  |                   |                     |                     |
  |                   | dispatch 1 resolved. we are inside        |
  |                   | Add.accept, so `this` is statically Add   |
  |                   |                     |                     |
  |                   |-- visitAdd(this) -->|                     |
  |                   |                     |                     |
  |                   |   dispatch 2 resolved. the runtime type   |
  |                   |   of `printer` picked Printer.visitAdd    |
  |                   |                     |                     |
  |                   |                     |-- left.accept(this) ->
  |                   |                     |                     |
  |                   |                     |<- visitLiteral(lit) -|
  |                   |                     |                     |
  |                   |                     |-- right.accept(this)->
  |                   |                     |<- visitLiteral(lit) -|
  |                   |                     |                     |
  |                   |<-- returns ---------|                     |
  |<-- returns -------|                     |                     |
```

Two timing notes. First, traversal is recursive and interleaved with the
operation. The visitor calls back into `accept` on children, so the call stack
depth is proportional to tree depth, which is the stack overflow failure mode in
dimension 11. Second, the visitor is a single mutable object shared across the
whole traversal, so it is not reentrant and not thread-safe unless written to be.

### The double dispatch call trace, step by step

This is the mechanism the entire pattern rests on, so it earns its own trace. The
question double dispatch answers is this. Which of the operation-times-node-type
bodies should run, when a single-dispatch language can only resolve one type per
call? Ingalls's 1986 answer is to spend two messages, each of which removes one
degree of polymorphism.

Start with two variables, each of unknown concrete type.

```
Static view at the call site
    Element  node    = <runtime type unknown, one of {Literal, Add, Neg}>
    Visitor  op      = <runtime type unknown, one of {Printer, Evaluator}>

    node.accept(op);        // we want the (Add, Printer) body. how?

STEP 1. The call node.accept(op)
    Single dispatch on the RECEIVER, `node`.
    The runtime looks up `accept` in the vtable of node's actual class.
    Say node is actually an Add. Control enters Add.accept.

    Degrees of polymorphism remaining. 1, because op is still unknown.
    What we have gained. inside Add.accept, `this` has STATIC type Add.
    The compiler now knows the element type. It is baked into the code.

STEP 2. The body of Add.accept, written once, in Add
        void accept(Visitor v) { v.visitAdd(this); }
                                   ^^^^^^^^  ^^^^
                                   |         |
                                   |         `this` is statically Add,
                                   |         so overload resolution or
                                   |         method naming is decided
                                   |         AT COMPILE TIME here.
                                   |
                                   method name chosen statically
                                   because we are inside Add

STEP 3. The call v.visitAdd(this)
    Single dispatch on the RECEIVER, `v`.
    The runtime looks up `visitAdd` in the vtable of v's actual class.
    Say v is actually a Printer. Control enters Printer.visitAdd(Add).

    Degrees of polymorphism remaining. 0. Both types are now fixed.
    The (Add, Printer) body is running.

NET RESULT
    Two single dispatches, chained, selected one of 3 x 2 = 6 bodies.
    Neither dispatch alone could do it.
    Dispatch 1 fixed the element type by ARRIVING somewhere.
    Dispatch 2 fixed the operation type by LEAVING from there.
```

Three consequences follow directly from that trace, and each one explains a rule
that otherwise looks arbitrary.

First, `accept` cannot be inherited from a shared base class. If `Add` and `Neg`
both inherited one `accept` body from `Element`, then `this` inside that body
would have static type `Element`, step 2 would have nothing to resolve, and the
mechanism collapses. Every concrete element must write its own one-line `accept`,
and that duplication is not an oversight in the pattern, it is load-bearing.

Second, the visitor method must be selected statically inside `accept`. Whether
the language does that by overload resolution on `visit(Add)` or by a distinct
name `visitAdd` is a style choice with a real consequence in Java, covered in
dimension 11 under the overload resolution failure.

Third, this generalises. Ingalls notes that the technique reduces higher degrees
of polymorphism as well, with each subsequent message dispatch removing one more
degree. Triple dispatch is three chained calls and a cubic number of bodies,
which is why nobody does it past two.

## 8. Implementation variants

**Classic external traversal, structure drives.** The ObjectStructure or the
client walks the tree and calls `accept` on each node. The visitor sees a flat
stream of nodes. The visitor cannot control descent, and it cannot know parent
context unless the structure supplies it. Good for filtering and collecting,
poor for anything needing scope.

**Classic internal traversal, elements drive.** Each composite element's `accept`
or the visitor's own visit method recurses into children. This is the form used
for syntax trees, because the visitor decides whether to descend, in what order,
and what state to push and pop around a subtree. It is also the form that
overflows the stack on deep input.

**Traversal by the visitor base class.** The abstract visitor implements every
visit method with a default that recurses into children and does nothing else.
Subclasses override only the node types they care about. This is the single most
practical variant and the one real libraries ship. Python's `ast.NodeVisitor`
documents exactly this contract, that `generic_visit` calls `visit` on all
children of the node, and that child nodes of nodes with a custom visitor method
are not visited unless the visitor calls `generic_visit` or visits them itself
(https://docs.python.org/3/library/ast.html, verified 2026-08-02). Roslyn's
`CSharpSyntaxWalker` is the same idea in C#. The cost is that the compile-time
exhaustiveness guarantee disappears, because a missing override silently inherits
the default.

**Visit methods returning a value.** The visit method returns a result type
instead of mutating visitor state. In a generic language this becomes
`Visitor<R>` with `R visitAdd(Add)`, and the operation is a fold over the tree
with no shared mutable state. Reentrant, thread-safe, and composable. The cost is
that a genuinely stateful operation has to thread its state through the return
type, and the generic signatures grow teeth.

**Visitor with a context parameter.** `R visitAdd(Add node, C context)`. Keeps
the visitor stateless while letting scope, depth and environment flow down the
tree. This is the shape most compiler passes converge on after their second
rewrite.

**Result-controlled traversal.** The visit method returns a value that tells the
traversal what to do next. Go's `go/ast.Visitor` returns another `Visitor` or
nil, documented as follows. If the visitor returned by `v.Visit(node)` is not
nil, Walk is invoked recursively with that visitor for each non-nil child,
followed by a call of `w.Visit(nil)` (https://pkg.go.dev/go/ast, verified
2026-08-02). Java's `FileVisitor` returns a `FileVisitResult` enum with values
including `CONTINUE`, `SKIP_SUBTREE` and `SKIP_SIBLINGS`
(https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/nio/file/FileVisitor.html,
verified 2026-08-02). Both give the visitor control over descent without giving
it the recursion itself, which is a good trade.

**Acyclic Visitor.** The variant written specifically to break the dependency
cycle. Martin's construction, from the paper cited in dimension 1, goes as
follows. Make the `Visitor` base class degenerate, with no member functions at
all, existing only as a placeholder in the type structure. Then declare one small
abstract visitor interface per concrete element, each holding a single `Visit`
method for that one element type. A concrete visitor inherits the degenerate base
plus only the per-element interfaces it actually wants to handle. Each element's
`accept` does a cross-cast, `dynamic_cast<HayesVisitor*>(&v)`, and calls `Visit`
when the cast succeeds. Martin's stated consequences are precise. All dependency
cycles are eliminated, derivatives of Element do not depend on each other,
recompilation is minimised, and partial visitation becomes natural with no extra
code, because a visitor that does not care about an element type simply does not
inherit that element's interface. The costs he lists are equally precise.
`dynamic_cast` can be expensive and its cost varies as the class hierarchy
changes, so the variant is a poor fit for hard real-time code; some languages
lack dynamic type resolution or multiple inheritance; and because there is one
abstract visitor class per element type, classes proliferate rapidly. The deeper
trade is that Acyclic Visitor converts a compile-time error, a missing method,
into a runtime outcome, a failed cast, which is the opposite of why many teams
adopted Visitor in the first place.

**Reflective or extrinsic Visitor.** No `accept` method exists. The visitor
inspects the runtime type itself, by a type switch, a map from class object to
handler, or a name-based lookup. Python's `NodeVisitor` is this variant, since
the default `visit` implementation calls the method named `visit_<classname>` or
falls back to `generic_visit` if that method does not exist. It is the only
option when the element classes cannot be modified. It costs static
exhaustiveness and adds reflection cost per node, and a typo in a method name
becomes a silently skipped node type.

**Visitor as a map of closures.** Instead of a class per operation, hold a
`Map<Class<?>, Function<Node, R>>` or a record of lambdas. Same double dispatch
through the map lookup, far less ceremony, and operations become values that can
be composed and partially overridden at runtime. Loses static checking entirely.

**Language note on Java 21 and later. The pattern is retired for closed
hierarchies.** A sealed interface plus a `switch` with type patterns gives
compile-time exhaustiveness with no `accept` method, no visitor interface, and no
double dispatch. Oracle's Java 21 documentation states that the compiler takes
into account whether the type of a selector expression is a sealed class, and
shows a switch over a sealed interface with three permitted subclasses that
compiles without a `default` label because its type coverage is exactly those
three classes
(https://docs.oracle.com/en/java/javase/21/language/pattern-matching-switch.html,
verified 2026-08-02). That is the same guarantee the visitor interface was being
used to obtain, delivered by the type system instead of by a class hierarchy. If
your element hierarchy can be sealed, write the switch.

**Language note on Rust. There is no classical form and none is wanted.** Rust
has no inheritance, and an `enum` with variants is the closed hierarchy directly.
The Rust book states that matches in Rust are exhaustive, meaning every last
possibility must be exhausted for the code to be valid, and shows the compiler
rejecting an incomplete match with `error[E0004]` for non-exhaustive patterns
(https://doc.rust-lang.org/book/ch06-02-match.html, verified 2026-08-02). Adding
a variant produces a compile error at every `match` that does not handle it,
which is precisely the property Visitor is built to buy. Rust's `syn` crate and
rustc's own AST do carry visitor traits, but for a different reason, to supply
default recursion over a very large node set, not to obtain dispatch.

**Language note on Kotlin.** Sealed classes plus `when` are the replacement. The
Kotlin documentation states that the `when` expression used with a sealed class
lets the compiler check exhaustively that all possible cases are covered, so no
`else` clause is needed (https://kotlinlang.org/docs/sealed-classes.html,
verified 2026-08-02).

**Language note on Swift.** An `enum` with associated values is the closed
hierarchy, and `switch` over it must be exhaustive. Swift Evolution proposal
SE-0192, "Handling Future Enum Cases" by Jordan Rose, implemented in Swift 5.0,
records the motivation for keeping that guarantee, that the feature helps prevent
bugs and makes it possible to enforce definitive initialization without having
`default` cases in every `switch`
(https://github.com/swiftlang/swift-evolution/blob/main/proposals/0192-non-exhaustive-enums.md,
verified 2026-08-02). The same proposal is why a `switch` over an enum from
another module needs `@unknown default`, which is the language admitting the
element set is open across a module boundary. That is the same limitation Visitor
has, made visible in the type system.

**Language note on TypeScript.** A discriminated union with a `never`-typed
exhaustiveness check in the default branch gives the compile-time guarantee with
no classes at all, and is the idiomatic form. The class-based Visitor survives in
TypeScript mostly in code ported from Java.

## 9. Known production uses

**Java NIO file tree walking, `java.nio.file.FileVisitor`.** The interface is
documented as a visitor of files, with an implementation provided to the
`Files.walkFileTree` methods to visit each file in a file tree. It declares four
operations, `preVisitDirectory`, `visitFile`, `visitFileFailed` and
`postVisitDirectory`, each returning a `FileVisitResult` that controls whether
traversal continues, skips the subtree, or skips siblings. This is a
production Visitor in the Java standard library with result-controlled traversal
and an explicit failure callback. Oracle, Java SE 21 API Specification,
`java.nio.file.FileVisitor`,
https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/nio/file/FileVisitor.html
verified 2026-08-02.

**Clang, `RecursiveASTVisitor`, used by every Clang-based analyser and tool.**
The Clang tooling documentation describes it as providing hooks of the form
`bool VisitNodeType(NodeType *)` for most AST node types, with `TypeLoc` nodes as
the exception because they are passed by value. A tool subclasses it, overrides
only the node types it cares about, and the base class supplies the recursion.
This is the traversal-in-the-base-class variant driving real static analysis over
C and C++ syntax trees. LLVM project, "How to write RecursiveASTVisitor based
ASTFrontendActions", https://clang.llvm.org/docs/RAVFrontendAction.html
verified 2026-08-02.

**Python standard library, `ast.NodeVisitor` and `ast.NodeTransformer`.**
`NodeVisitor` is documented as a base class for walking abstract syntax trees,
dispatching by calling `self.visit_<classname>` for the node class, or
`generic_visit` when no such method exists. `NodeTransformer` is a `NodeVisitor`
subclass that allows modification of nodes, using the return value of the visitor
method to replace the node, or removing the node when the method returns `None`.
This is the reflective variant, and the transformer subclass is the
result-returning variant used for real source rewriting. Python Software
Foundation, Python 3 documentation, `ast` module,
https://docs.python.org/3/library/ast.html verified 2026-08-02.

**Go standard library, `go/ast.Visitor` and `ast.Walk`.** The interface is
declared as a single `Visit` method taking a `Node` and returning a `Visitor`,
and `Walk` is documented as traversing an AST in depth-first order, calling
`v.Visit(node)`, and, when the returned visitor `w` is not nil, recursing with
`w` for each non-nil child followed by a call of `w.Visit(nil)`. The
returned-visitor idiom lets a visitor swap itself out for a subtree and receive a
scope-exit notification, which is Visitor adapted to a language without
inheritance. Go project, `go/ast` package documentation, https://pkg.go.dev/go/ast
verified 2026-08-02.

**Roslyn, the .NET compiler platform, `CSharpSyntaxWalker`.** Documented as
representing a `CSharpSyntaxVisitor` that descends an entire `CSharpSyntaxNode`
graph, visiting each node and its child nodes and tokens in depth-first order.
Every Roslyn analyser and code-fix provider that inspects syntax is built on this
type or its `CSharpSyntaxRewriter` sibling. Microsoft, .NET API documentation,
`Microsoft.CodeAnalysis.CSharp.CSharpSyntaxWalker`,
https://learn.microsoft.com/en-us/dotnet/api/microsoft.codeanalysis.csharp.csharpsyntaxwalker
verified 2026-08-02.

## 10. Consequences

Positive.

- Adding an operation costs one new class and touches no existing file. This is
  the Open Closed Principle applied along the operation axis.
- All the cases of one operation live together, so they can share private helper
  methods, private state, and a single coherent set of imports. A twenty-node
  pretty-printer is one readable file instead of twenty scattered methods.
- The element classes stay a data model. They do not import the rendering
  library, the persistence format, or the cost model.
- In the classic statically typed form, the compiler refuses to build a visitor
  that has not handled every element type, which converts a class of runtime bugs
  into build failures.
- Traversal state has an obvious home, the visitor instance, which makes
  operations needing a symbol table, a depth counter or an error list natural to
  write.
- Operations become first-class objects, so they can be selected at runtime,
  composed, decorated, logged, or queued as Commands.

Negative.

- Adding an element type is a breaking change to the visitor interface, and
  breaks every implementation in every repository that has one. On a published
  API this is the pattern's largest cost.
- The dependency cycle described in dimension 5 means the element base type
  transitively depends on all of its own subtypes, which slows builds and blocks
  clean module boundaries. This is the problem Acyclic Visitor exists to solve.
- Encapsulation is weakened. The element must expose whatever any operation might
  need, which grows its public surface over time.
- Two virtual calls per node instead of one, and the visit call site is
  megamorphic.
- The code is harder to read for anyone who does not already know the pattern,
  and the one-line `accept` bodies look like pointless indirection until the
  reader understands step 2 of the trace in dimension 7.
- Boilerplate scales as the product of element types and traversal-defaulting
  choices, and the `accept` method must be duplicated, correctly, in every
  concrete element.
- A visitor instance is stateful and therefore usually single-use and not
  thread-safe, which is a constraint callers must know and cannot see.

## 11. Failure modes and misuse

Symptom, cause, fix. The symptoms are the observable ones, drawn from practice
rather than from a source.

**Copy-paste `accept` calling the wrong visit method.** Symptom. One node type is
silently handled as another. A `Subtract` node prints as `Add`, or the evaluator
returns a plausible but wrong number, with no error and no exception anywhere.
Cause. `Subtract.accept` was copied from `Add.accept` and the body still says
`v.visitAdd(this)`. The compiler accepts it whenever the visitor methods share a
name or the parameter types are related. Fix. A test per concrete element
asserting that `accept` reaches the matching visit method, using a recording
visitor. This is five lines per element and it catches the whole class.

**Inherited `accept` collapses the dispatch.** Symptom. Every node in a subtree
hits the same visit method, the one for the shared base class, and the specific
handlers never run. Cause. `accept` was written once in an intermediate abstract
class to remove duplication, so `this` has the static type of that intermediate
class at the call site. Fix. Restore the per-class `accept`. The duplication is
the mechanism, see dimension 7.

**Java overload resolution picks the base overload.** Symptom. The same silent
misdispatch as above, in code where `accept` was written correctly, and it
appears only after someone changed a field's declared type from `Add` to
`Element`. Cause. Java resolves overloads on the static type of the argument at
compile time. `v.visit(this)` inside a correctly written `accept` is fine, but
`v.visit(someElementTypedVariable)` binds to `visit(Element)` forever. Fix. Give
the visit methods distinct names, `visitAdd`, `visitNeg`, so a mistake becomes a
compile error rather than a wrong binding. This is why real Java visitor
interfaces almost always use distinct names.

**Stack overflow on deep input.** Symptom. A `StackOverflowError` or a segfault
on one customer's file, usually a machine-generated one, while every hand-written
input works. Cause. Internal recursive traversal on a left-leaning tree of ten
thousand binary operators, giving a stack depth of ten thousand frames doubled by
the accept-visit pair. Fix. Convert the hot traversal to an explicit worklist
with a heap-allocated stack, or impose a depth limit that fails with a clear
message rather than crashing.

**Missing case silently ignored.** Symptom. A new node type produces no output,
no error, and no log line. Noticed weeks later when someone sees that a section
of a report is empty. Cause. The traversal-in-the-base-class variant, where the
default `generic_visit` recursion is inherited by a subclass that meant to
override it. The compile-time guarantee was traded away when the default was
added, and nobody saw it happen. Fix. Make the default throw for node types the
operation genuinely cannot handle, or add a test that runs every visitor over a
fixture tree containing one instance of every element type.

**The interface everyone breaks.** Symptom. A one-line feature in the core
library produces a pull request touching forty files across eight repositories,
and the release is blocked for a week on downstream coordination. Cause. A new
element type was added to a hierarchy whose visitor interface is public API. Fix.
Nothing cheap at this point. Prevention is the choice in dimension 4, and the
mitigations are a default-implementing abstract visitor base class, which trades
the guarantee for compatibility, or Acyclic Visitor, which trades it for a
runtime cast.

**The visitor that reaches back into the structure.** Symptom. Modifying a
collection while visiting it throws a concurrent modification error, or a
rewriting visitor produces a tree with a cycle in it and the next traversal never
terminates. Cause. The visitor mutates the structure it is traversing. Fix. Build
a new tree and return it, the `NodeTransformer` shape, or collect the mutations
during the walk and apply them after it finishes.

**Visitor reused across traversals.** Symptom. The second report contains the
first report's rows, or a counter reads double. Cause. The visitor accumulates
state in fields and the caller kept the instance. Fix. Construct a fresh visitor
per traversal, or add an explicit `reset`, and document which one the type
supports. The result-returning variant removes the failure mode entirely.

**Megamorphic call site slowdown.** Symptom. A traversal that benchmarks well on
a two-node-type fixture runs several times slower on real input, with profiles
showing time in dispatch rather than in the visit bodies. Cause. The `accept`
call site sees many receiver types, so the runtime cannot use a monomorphic or
bimorphic inline cache and falls back to a full virtual lookup, and the visit
bodies stop being inlined into the caller. Fix. Measure before caring. If it is
real, the answers are a flattened representation such as a tagged array with an
index-based switch, or splitting the hot node types out of the general path.

**Visitor used to fake a missing feature.** Symptom. A visitor interface with two
methods, `visitA` and `visitB`, and one implementation. Cause. The pattern was
applied by reflex to a two-type hierarchy. Fix. Delete it and write a type
switch, or a sealed hierarchy with a `switch` if the language has one.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3. All
alternatives here are real designs that solve the same problem.

| Force | Visitor (classic) | Acyclic Visitor (Martin) | Sealed type plus exhaustive switch | Method per operation on Element | Type switch, no exhaustiveness check | Map of class to handler closure |
|---|---|---|---|---|---|---|
| Cost of adding an operation | One new class, no edits | One new class, no edits | One new function, no edits | Edit every element class | One new function, no edits | One new map, no edits |
| Cost of adding an element type | Breaks every visitor at compile time | New element plus its abstract visitor, existing visitors unaffected | Compile error at every switch, in one repo | One method per operation on the new class | Silent fallthrough at runtime | Silent miss at runtime |
| Missing case detected | At compile time | At runtime, failed cast | At compile time | At compile time | Not detected | Not detected |
| Source dependency shape | Cycle, Element depends on its own subtypes | Acyclic by construction | Acyclic, sealed type names its own permits | Acyclic | Acyclic | Acyclic |
| Cohesion of one operation | Strong, one file | Strong, one file | Strong, one function | Weak, scattered across element files | Strong, one function | Strong, one map |
| Encapsulation of elements | Weakened, must expose internals | Weakened, same reason | Weakened, same reason | Preserved, the method is inside | Weakened, same reason | Weakened, same reason |
| Latency per node | Two virtual calls, megamorphic | Two calls plus a dynamic cast | One switch, often a jump table | One virtual call | One chain of type tests | One hash lookup plus a call |
| Cognitive load | High, indirect and unfamiliar | Very high, cross-casts and many types | Low, reads top to bottom | Low per method, high across the model | Low | Medium |
| Class or type count | Plus one visitor interface, plus one class per operation | Plus one abstract visitor per element type as well | No new types | No new types | No new types | No new types |
| Works on types you do not own | No, needs `accept` | No, needs `accept` | Only if you can seal them | Yes | Yes | Yes |
| Language requirement | Single dispatch and subtyping | Multiple inheritance and safe cross-cast | Sealed types and pattern matching | Subtyping | Runtime type test | Runtime type identity |
| Traversal state has a home | Yes, visitor fields | Yes, visitor fields | No, thread it through parameters | No | No | No |

Reading of the table. Visitor wins when the language lacks sealed types, the
element set is closed, and compile-time exhaustiveness is worth its price.
Acyclic Visitor wins when the element set is not closed and build coupling is the
main pain, at the cost of moving the check to runtime. The sealed type plus
exhaustive switch wins outright wherever the language offers it and the hierarchy
can be sealed, which is why the pattern is in retreat. Method per operation on
the element wins when there are few operations and they genuinely belong to the
data. The plain type switch wins for a small closed set where a missed case is
cheap. The closure map wins where operations must be registered at runtime, for
example by plugins.

## 13. Related and incompatible patterns

- **Composite.** The classic host. Visitor is written over a Composite tree far
  more often than over a flat collection, because a tree is where the many-types
  many-operations problem actually arises. Composite supplies the structure and
  Visitor supplies the operations, and each composite element's `accept` is
  responsible for recursing into children in the internal-traversal variant. The
  GoF catalog pairs them explicitly.
- **Interpreter.** Visitor is the standard way to add operations to an
  Interpreter's expression hierarchy without putting every operation in the
  `interpret` method. A type checker, a constant folder and an evaluator over the
  same grammar are three visitors.
- **Iterator.** Complementary and frequently confused. Iterator decides the order
  in which elements are reached. Visitor decides which code runs when one is
  reached. A Visitor over a homogeneous list is an Iterator with extra vocabulary
  and no benefit, which is the misuse in dimension 4.
- **Strategy.** Overlaps at the small end. One operation over one element type is
  a Strategy. Visitor is what Strategy becomes when the operation must vary with
  the element type as well as with the caller's intent.
- **Template Method.** Composes cleanly. The abstract visitor's traversal
  defaults are a template method, with the per-node visit methods as hooks. This
  is exactly the `RecursiveASTVisitor` and `CSharpSyntaxWalker` shape from
  dimension 9.
- **Command.** A concrete visitor is often also a Command, an operation
  reified as an object. If the operations need to be queued, undone or replayed,
  the two patterns land on the same class and the combination is natural.
- **Interpreter versus Visitor as a fork.** They are alternatives for the same
  code when the operation set is small and stable. Putting `interpret` on the
  node is simpler; pulling it into a visitor pays off at the third operation.
- **Sealed hierarchy plus pattern matching.** The direct replacement, not a
  collaborator. Where the language offers it and the hierarchy can be sealed, it
  supersedes Visitor on every force in dimension 12 except one, that it has no
  natural home for traversal state.
- **Multimethods and generic functions.** The language feature Visitor
  approximates. Common Lisp's CLOS generic functions, Julia's multiple dispatch,
  and Clojure's `defmulti` dispatch on the runtime types of several arguments
  directly. In such a language Visitor is unnecessary, and writing it is a
  translation artefact from a single-dispatch language.
- **Service Locator.** Conflicts in practice. A visitor that resolves its
  collaborators from a global locator inside its visit methods becomes untestable
  in isolation, which discards the pattern's main testability benefit.
- **Anaemic Domain Model.** A related risk rather than a pattern that composes.
  Pushing every behaviour out of the element classes into visitors, past the point
  where the behaviour genuinely does not belong to the data, produces element
  classes that are bags of getters. Visitor is a tool for operations that are
  foreign to the model, not a licence to empty the model.

## 14. Refactoring path in and out

Introducing the pattern into a hierarchy that has accumulated operations as
methods. The relevant named refactorings are Extract Class and Move Method, see
the refactoring family entries. Ordered steps, each one keeping the build green.

1. Pick one operation that clearly does not belong to the data. The best first
   candidate is the one whose implementation pulls the most foreign imports into
   the element files, for example a serialiser or a renderer.
2. Confirm the element set is closed enough to pay for the pattern. If a new
   element type is planned for this quarter, stop here and reconsider against
   dimension 4.
3. Add the `Visitor` interface with one method per concrete element type, and add
   `accept` to the element base type. Give every concrete element its own
   one-line `accept`. Do not move any logic yet. Run the tests. At this point the
   build is heavier and nothing has improved, which is normal.
4. Add the per-element `accept` dispatch test from dimension 11 now, before any
   logic depends on the dispatch being correct.
5. Create the concrete visitor for the chosen operation. Move the body of each
   element's method into the matching visit method, one element at a time,
   running the tests after each move. Where the moved body touched a private
   field, add the narrowest accessor that satisfies it and note the encapsulation
   cost.
6. Change the call sites from `element.doThing()` to
   `element.accept(new ThingVisitor())`. Delete the now-empty methods from the
   element classes.
7. Repeat from step 5 for the second operation. The second operation is where the
   pattern starts paying, because it costs one file and touches nothing else. If
   there is no second operation, revert the whole change.

Removing the pattern when it stops earning its place. The signals are a visitor
interface that has changed three times in a year, a single concrete visitor, or a
language upgrade that brought sealed types.

1. Establish whether the element hierarchy can be sealed. In Java, Kotlin, Scala
   or C#, seal the base type and list the permitted subtypes. In Rust, Swift or
   TypeScript, the equivalent is an enum or a discriminated union, which may be a
   larger change.
2. Convert one concrete visitor to a function taking the element and switching
   over it with type patterns. Keep the visitor in place and delegate to the new
   function, so both paths are live and the tests cover both.
3. Confirm the compiler reports exhaustiveness on the new switch, by deliberately
   deleting one case and checking that the build fails. If it does not fail, the
   sealing is incomplete and step 1 is not finished.
4. Move the call sites to the function. Delete the concrete visitor.
5. Repeat for every visitor. When the last one is gone, delete the `Visitor`
   interface and every `accept` method. This is Inline Method applied to `accept`,
   plus Remove Middle Man, see the refactoring family entries for both.
6. If the hierarchy cannot be sealed but the build coupling is the problem, the
   move is to Acyclic Visitor rather than out of the pattern, and it is a
   different refactoring, splitting the visitor interface into one interface per
   element type and changing `accept` to a cross-cast.

## 15. Testing and verification

This dimension is practice rather than a sourced claim.

Easier because of the pattern.

- A concrete visitor is a plain object with no dependency on the rest of the
  system. Constructing one, feeding it a hand-built tree and asserting on its
  output is two lines of setup and needs no mocking framework, no container and
  no database.
- The operation under test is one file, so its test is one file, and the mapping
  between them is obvious to a reader.
- Test doubles fall out for free. A recording visitor that appends each visited
  node to a list is the cheapest way to assert traversal order, dispatch
  correctness and descent control, and it is a real implementation rather than a
  mock.
- Because operations are objects, a property test can generate random trees and
  run several visitors over each one, asserting relationships between them, for
  example that the pretty-printer's output reparses to a tree the evaluator
  scores identically.

Harder because of the pattern.

- Coverage becomes two-dimensional. A test that exercises every element type and
  a test that exercises every operation together still leave most of the
  element-times-operation grid untouched. Deciding which cells matter is a
  judgement call that a coverage percentage does not make for you.
- Failures are further from their cause. A wrong result surfaces in the visitor,
  while the bug may be in an `accept` body one hop away and in another file.
- Traversal and operation are entangled in the internal-traversal variant, so a
  test of the operation is also a test of the traversal, and a traversal bug
  looks like an operation bug.

Techniques that apply.

- **Dispatch test per concrete element.** For each element type, call `accept`
  with a recording visitor and assert exactly which visit method fired. This is
  the direct defence against the copy-paste and inheritance failures in dimension
  11, and it is mechanical enough to generate.
- **Exhaustiveness fixture.** Build one tree containing at least one instance of
  every element type, and run every visitor over it in a parameterised test. In
  the default-implementing variant, where the compiler no longer helps, this
  fixture is the only thing standing between you and the silently ignored node.
  Add a test that fails when a new element type is added without being added to
  the fixture, for example by reflecting over the sealed subtype list.
- **Contract test over the visitor interface.** Write one abstract test class
  stating the invariants every visitor must satisfy, for example that visiting a
  node twice with a fresh visitor gives the same answer, then subclass it once
  per concrete visitor.
- **Golden-file tests for printers and serialisers.** Printing visitors are
  ideally suited to snapshot testing, because the whole output is the assertion
  and diffs are readable.
- **Round-trip property.** Where a printing visitor and a parser exist, assert
  that parse of print of tree equals tree, over generated trees. This finds
  precedence and escaping bugs no per-node test will.
- **Depth stress test.** Generate a deliberately deep tree, ten thousand nodes on
  one spine, and assert the traversal either completes or fails with your own
  clear error rather than a stack overflow.

## 16. Observability signals

The pattern hides which body ran, so telemetry has to say it, otherwise nobody
can diagnose a traversal from production data. This dimension is practice.

What to record.

- A counter of visit calls, labelled by operation name and element type. This
  two-label counter is the single most useful signal, because the shape of the
  distribution is the shape of the input, and an unexpected element type or a
  missing one is visible at a glance.
- One span per traversal, not per node, carrying the operation name, the node
  count, the maximum depth reached, and the duration. Per-node spans are almost
  always the wrong choice, because a traversal of a hundred thousand nodes
  produces a trace nobody can open.
- A histogram of tree depth and node count per traversal. The tail of the depth
  histogram is the early warning for the stack overflow failure in dimension 11,
  and it moves before the crash does.
- A counter of default or fallback visits in the default-implementing variant,
  labelled by element type. In a healthy system this counter is either zero or a
  known constant, and any movement means a node type is being silently ignored.
- A counter of visitor errors, labelled by operation and element type, so a
  failure localises to one cell of the grid rather than to the traversal as a
  whole.
- For the Acyclic Visitor variant, a counter of failed cross-casts. Because the
  variant converts a compile error into a runtime one, this counter is the only
  place the missing case appears.

A healthy instance on a dashboard. The per-element-type visit counter holds a
stable ratio that reflects the corpus being processed, and moves only when the
input mix or a deployment explains it. Traversal duration scales linearly with
node count, so a scatter of duration against node count is a straight line.
Maximum depth sits well inside a known bound. The fallback counter is flat at its
expected value.

A failing instance. An element type appears in the counter that should not exist
in this environment, which means a producer upstream is emitting a node the
operation was never designed for. Or the fallback counter starts climbing after a
deploy, which is the silently ignored node type, and it climbs on exactly the
operations whose authors forgot the override. Or duration stops scaling linearly
with node count, which points at quadratic behaviour introduced by a visitor that
rescans a subtree per node. Or the depth histogram grows a long tail while node
count is flat, which means input shape has changed and the stack overflow is
coming. Or one cell of the operation-by-element error counter lights up alone,
which localises the bug to a single visit method without reading any code.

## 17. Security and privacy implications

This dimension is analytical rather than sourced, and the pattern is close to
silent on security in its closed form, where all elements and all visitors ship
in one build. Four genuine implications appear once the structure or the visitor
set is open.

**Unbounded recursion as a denial of service.** The internal-traversal variant
recurses once per level of the input structure, and in most languages the stack
is a fixed resource that cannot be caught reliably. If the structure is parsed
from attacker-controlled input, for example JSON, XML, a query language, or a
source file, an input consisting of ten thousand nested brackets converts into
ten thousand stack frames and terminates the process or the thread. This is a
real and frequently exploited shape. The defence is a depth limit applied during
parsing, before any visitor runs, plus an explicit worklist traversal in the
visitors that run on untrusted input.

**Untrusted visitor implementations.** A published visitor interface is an
extension point that third-party code implements and your traversal then calls,
once per node, with a live reference to that node. The visitor runs inside your
process with your privileges and receives every element in the structure, which
means a plugin visitor sees data the plugin was never intended to see. If
visitors can be loaded from disk or a package registry, treat the interface as an
untrusted boundary, pass the narrowest view of each element that the operation
needs, and apply the same supply-chain controls you would to any loaded code.

**Data exposure through the widened element surface.** Dimension 10 records that
Visitor weakens encapsulation, because elements must expose whatever any
operation might need. That accessor added for the cost estimator is also visible
to the logging visitor and to any future visitor written by anyone. On a
structure carrying personal data, a field opened up for one operation becomes
reachable by all of them, and the audit question of who can read this field stops
having a small answer. The mitigation is to keep sensitive fields behind
purpose-shaped accessors that return a redacted or derived value, rather than a
general getter.

**Cross-cast dispatch in the Acyclic variant.** Martin's construction resolves
which visit method runs by a runtime cast rather than by a compile-time method
table. A visitor that is only partially implemented silently does nothing for the
element types it does not handle. In a security-relevant operation, for example a
policy checker or a redactor, silently doing nothing is the wrong default and
means an unrecognised node type passes unchecked. Make the failed-cast branch
fail closed, and count it, per dimension 16.

On privacy the pattern is otherwise neutral, with one practical caveat carried
over from dimension 16. The advice there is to label metrics by element type. An
element type name can encode a document category, a customer tier or a data
classification. Where the names carry that, treat the label as attributable data
and apply the same retention and access rules as to any other identifier.

## Code examples

Six languages, chosen to show the pattern in three different lights. Java shows
the classical form with distinct method names, and then the Java 21 replacement
that retires it. TypeScript shows the classical form and the discriminated-union
alternative. Python shows the reflective, dispatch-by-name form that the standard
library uses. Go shows the returned-visitor form with no inheritance available.
Rust and Swift show why the pattern does not exist there, each for the same
reason, a closed sum type plus an exhaustive match.

Every sample below was compiled and run on 2026-08-02 on the authoring machine.
Nothing here is untested. The verification results, including the deliberate
negative tests that prove the exhaustiveness claims in dimension 8.

| Sample | Toolchain | Result |
|---|---|---|
| Java, classical form | OpenJDK 26.0.2, `javac` then `java` | Printed `(3 + -4)` then `-1` |
| Java 21, sealed switch | OpenJDK 26.0.2, `javac --release 21` | Printed `(3 + -4)` then `-1` |
| Java 21, one case deleted | same | Build failed with `error: the switch expression does not cover all possible input values` |
| TypeScript, classical | TypeScript 7.0.2, `tsc --strict` | Type-checked with zero errors |
| TypeScript, union | TypeScript 7.0.2, compiled then `node` | Printed `-1` |
| TypeScript, one case deleted | same | Build failed with `error TS2322: Type '{ kind: "neg"; inner: ExprNode; }' is not assignable to type 'never'` |
| Python, reflective | CPython 3, `python3` | Printed `(3 + -4)` then `-1` |
| Go, returned visitor | `go run` | Printed `literals=2 operators=2` |
| Rust, match | `rustc` | Printed `(3 + -4)` then `-1` |
| Rust, one arm deleted | `rustc` | Build failed with `error[E0004]: non-exhaustive patterns: &Node::Neg(_) not covered` |
| Swift, match | Apple Swift 6.3.2, `swiftc` | Printed `(3 + -4)` then `-1` |
| Swift, one case deleted | same | Build failed with `error: switch must be exhaustive` |

C# and Kotlin are discussed in dimension 8 but no sample is given for them,
because no compiler for either language was available on the authoring machine
and an unverified sample would be worse than none.

### Java, classical form

```java
import java.util.List;

interface Visitor {
    String visitLiteral(Literal e);
    String visitAdd(Add e);
    String visitNeg(Neg e);
}

abstract class Expr {
    abstract String accept(Visitor v);
}

final class Literal extends Expr {
    final int value;
    Literal(int value) { this.value = value; }
    // This one line is dispatch step 2. It cannot be inherited.
    String accept(Visitor v) { return v.visitLiteral(this); }
}

final class Add extends Expr {
    final Expr left, right;
    Add(Expr left, Expr right) { this.left = left; this.right = right; }
    String accept(Visitor v) { return v.visitAdd(this); }
}

final class Neg extends Expr {
    final Expr inner;
    Neg(Expr inner) { this.inner = inner; }
    String accept(Visitor v) { return v.visitNeg(this); }
}

final class Printer implements Visitor {
    public String visitLiteral(Literal e) { return Integer.toString(e.value); }
    public String visitAdd(Add e) {
        return "(" + e.left.accept(this) + " + " + e.right.accept(this) + ")";
    }
    public String visitNeg(Neg e) { return "-" + e.inner.accept(this); }
}

final class Evaluator implements Visitor {
    public String visitLiteral(Literal e) { return Integer.toString(e.value); }
    public String visitAdd(Add e) {
        int l = Integer.parseInt(e.left.accept(this));
        int r = Integer.parseInt(e.right.accept(this));
        return Integer.toString(l + r);
    }
    public String visitNeg(Neg e) {
        return Integer.toString(-Integer.parseInt(e.inner.accept(this)));
    }
}

public final class VisitorDemo {
    public static void main(String[] args) {
        Expr tree = new Add(new Literal(3), new Neg(new Literal(4)));
        for (Visitor v : List.of(new Printer(), new Evaluator())) {
            System.out.println(tree.accept(v));
        }
    }
}
```

### Java 21, the replacement that retires the pattern

No `accept`, no visitor interface, no double dispatch, and the compiler still
refuses a switch that misses a case.

```java
sealed interface Node permits Lit, Sum, Negate {}
record Lit(int value) implements Node {}
record Sum(Node left, Node right) implements Node {}
record Negate(Node inner) implements Node {}

public final class SealedDemo {
    // No default label. Removing one case is a compile error.
    static int eval(Node n) {
        return switch (n) {
            case Lit l -> l.value();
            case Sum s -> eval(s.left()) + eval(s.right());
            case Negate g -> -eval(g.inner());
        };
    }

    static String print(Node n) {
        return switch (n) {
            case Lit l -> Integer.toString(l.value());
            case Sum s -> "(" + print(s.left()) + " + "
                              + print(s.right()) + ")";
            case Negate g -> "-" + print(g.inner());
        };
    }

    public static void main(String[] args) {
        Node tree = new Sum(new Lit(3), new Negate(new Lit(4)));
        System.out.println(print(tree));
        System.out.println(eval(tree));
    }
}
```

### TypeScript, classical form and the union alternative

```typescript
interface Visitor<R> {
  visitLiteral(e: Literal): R;
  visitAdd(e: Add): R;
  visitNeg(e: Neg): R;
}

interface Expr {
  accept<R>(v: Visitor<R>): R;
}

class Literal implements Expr {
  constructor(readonly value: number) {}
  accept<R>(v: Visitor<R>): R { return v.visitLiteral(this); }
}

class Add implements Expr {
  constructor(readonly left: Expr, readonly right: Expr) {}
  accept<R>(v: Visitor<R>): R { return v.visitAdd(this); }
}

class Neg implements Expr {
  constructor(readonly inner: Expr) {}
  accept<R>(v: Visitor<R>): R { return v.visitNeg(this); }
}

class Printer implements Visitor<string> {
  visitLiteral(e: Literal): string { return String(e.value); }
  visitAdd(e: Add): string {
    return `(${e.left.accept(this)} + ${e.right.accept(this)})`;
  }
  visitNeg(e: Neg): string { return `-${e.inner.accept(this)}`; }
}

class Evaluator implements Visitor<number> {
  visitLiteral(e: Literal): number { return e.value; }
  visitAdd(e: Add): number {
    return e.left.accept(this) + e.right.accept(this);
  }
  visitNeg(e: Neg): number { return -e.inner.accept(this); }
}

const tree: Expr = new Add(new Literal(3), new Neg(new Literal(4)));
console.log(tree.accept(new Printer()), tree.accept(new Evaluator()));
```

The idiomatic TypeScript replacement uses a discriminated union and a
`never`-typed guard, which fails the build when a variant is added and a case is
missed.

```typescript
type ExprNode =
  | { kind: "lit"; value: number }
  | { kind: "sum"; left: ExprNode; right: ExprNode }
  | { kind: "neg"; inner: ExprNode };

function evaluate(n: ExprNode): number {
  switch (n.kind) {
    case "lit": return n.value;
    case "sum": return evaluate(n.left) + evaluate(n.right);
    case "neg": return -evaluate(n.inner);
    default: {
      const unreachable: never = n;
      return unreachable;
    }
  }
}

const t: ExprNode = { kind: "sum", left: { kind: "lit", value: 3 },
                      right: { kind: "neg",
                               inner: { kind: "lit", value: 4 } } };
console.log(evaluate(t));
```

The name `ExprNode` rather than `Node` is deliberate. TypeScript's DOM library
already declares a global `Node`, and reusing the name produces a duplicate
identifier error before any of the union logic is reached.

### Python, the reflective form the standard library uses

```python
class Node:
    pass


class Lit(Node):
    def __init__(self, value: int) -> None:
        self.value = value


class Sum(Node):
    def __init__(self, left: Node, right: Node) -> None:
        self.left, self.right = left, right


class Neg(Node):
    def __init__(self, inner: Node) -> None:
        self.inner = inner


class NodeVisitor:
    # Dispatch by name, the ast.NodeVisitor contract. No accept method needed.
    def visit(self, node: Node):
        name = "visit_" + type(node).__name__
        return getattr(self, name, self.generic_visit)(node)

    def generic_visit(self, node: Node):
        raise NotImplementedError(f"no handler for {type(node).__name__}")


class Printer(NodeVisitor):
    def visit_Lit(self, n: Lit) -> str:
        return str(n.value)

    def visit_Sum(self, n: Sum) -> str:
        return f"({self.visit(n.left)} + {self.visit(n.right)})"

    def visit_Neg(self, n: Neg) -> str:
        return f"-{self.visit(n.inner)}"


class Evaluator(NodeVisitor):
    def visit_Lit(self, n: Lit) -> int:
        return n.value

    def visit_Sum(self, n: Sum) -> int:
        return self.visit(n.left) + self.visit(n.right)

    def visit_Neg(self, n: Neg) -> int:
        return -self.visit(n.inner)


if __name__ == "__main__":
    tree = Sum(Lit(3), Neg(Lit(4)))
    print(Printer().visit(tree))
    print(Evaluator().visit(tree))
```

Note the cost this variant pays. A typo in `visit_Neg` does not fail at import
time, it falls through to `generic_visit`, which is why the fallback raises
rather than returning `None`.

### Go, the returned-visitor form

Go has no inheritance, so the classical form does not exist. The standard
library's shape, a `Visit` method returning the visitor to use for children, is
the idiomatic translation.

```go
package main

import "fmt"

type Node interface{ children() []Node }

type Lit struct{ Value int }
type Sum struct{ Left, Right Node }
type Neg struct{ Inner Node }

func (l Lit) children() []Node { return nil }
func (s Sum) children() []Node { return []Node{s.Left, s.Right} }
func (n Neg) children() []Node { return []Node{n.Inner} }

type Visitor interface{ Visit(n Node) Visitor }

// Walk mirrors go/ast.Walk. A nil return stops descent into that subtree.
func Walk(v Visitor, n Node) {
	if v = v.Visit(n); v == nil {
		return
	}
	for _, c := range n.children() {
		Walk(v, c)
	}
	v.Visit(nil)
}

type counter struct{ lits, ops int }

func (c *counter) Visit(n Node) Visitor {
	switch n.(type) {
	case Lit:
		c.lits++
	case Sum, Neg:
		c.ops++
	}
	return c
}

func main() {
	tree := Sum{Left: Lit{3}, Right: Neg{Inner: Lit{4}}}
	c := &counter{}
	Walk(c, tree)
	fmt.Printf("literals=%d operators=%d\n", c.lits, c.ops)
}
```

### Rust, where the pattern does not exist

Included to make the point concrete rather than to demonstrate a Visitor. The
enum is the closed hierarchy and `match` is the exhaustive dispatch, so there is
nothing left for the pattern to buy.

```rust
enum Node {
    Lit(i32),
    Sum(Box<Node>, Box<Node>),
    Neg(Box<Node>),
}

fn eval(n: &Node) -> i32 {
    match n {
        Node::Lit(v) => *v,
        Node::Sum(l, r) => eval(l) + eval(r),
        Node::Neg(i) => -eval(i),
    }
}

fn print(n: &Node) -> String {
    match n {
        Node::Lit(v) => v.to_string(),
        Node::Sum(l, r) => format!("({} + {})", print(l), print(r)),
        Node::Neg(i) => format!("-{}", print(i)),
    }
}

fn main() {
    let tree = Node::Sum(
        Box::new(Node::Lit(3)),
        Box::new(Node::Neg(Box::new(Node::Lit(4)))),
    );
    println!("{}", print(&tree));
    println!("{}", eval(&tree));
}
```

### Swift, the same conclusion by a different route

An `indirect enum` gives the recursive closed hierarchy, and `switch` over it
must be exhaustive, so the pattern buys nothing inside a module. The `indirect`
keyword is what allows a case to hold the enum itself, which is the boxing that
Rust spells out with `Box`.

```swift
indirect enum Node {
    case lit(Int)
    case sum(Node, Node)
    case neg(Node)
}

func eval(_ n: Node) -> Int {
    switch n {
    case .lit(let v): return v
    case .sum(let l, let r): return eval(l) + eval(r)
    case .neg(let i): return -eval(i)
    }
}

func render(_ n: Node) -> String {
    switch n {
    case .lit(let v): return String(v)
    case .sum(let l, let r): return "(\(render(l)) + \(render(r)))"
    case .neg(let i): return "-\(render(i))"
    }
}

let tree = Node.sum(.lit(3), .neg(.lit(4)))
print(render(tree))
print(eval(tree))
```

The limit is the one dimension 8 records from SE-0192. This guarantee holds
inside a module. A `switch` over an enum imported from another module needs
`@unknown default`, because across that boundary the case set is open again,
which is the same openness that makes Visitor's element interface a breaking
change.

## 18. References

1. Erich Gamma, Richard Helm, Ralph Johnson, John Vlissides. *Design Patterns.
   Elements of Reusable Object-Oriented Software*. Addison-Wesley, 1994.
   ISBN 0-201-63361-2. Chapter 5, Behavioral Patterns, section Visitor. Source of
   the intent, the five participants, the pairing with Composite and Interpreter,
   and the broken-encapsulation consequence. The page reference, p. 331 in the
   1995 printing, is taken from footnote 2 of reference 3 rather than verified
   against a copy of the book.
2. Daniel H. H. Ingalls. "A Simple Technique for Handling Multiple Polymorphism".
   *OOPSLA '86 Proceedings*, ACM, September 1986, page 347.
   ACM 0-89791-204-7/86/0900-0347.
   https://algoritmos-iii.github.io/assets/bibliografia/simple-technique-for-handling-multiple-polymorphism.pdf
   Verified 2026-08-02 by reading page 347 of the scanned proceedings. Source for
   the double dispatch mechanism predating the catalog, the statement of the
   multiply polymorphic problem, and the reduction of higher degrees of
   polymorphism by chained dispatch.
3. Robert C. Martin. *Acyclic Visitor* (v1.0). Object Mentor. No publication date
   printed on the paper.
   https://condor.depaul.edu/dmumaugh/OOT/Design-Principles/acv.pdf
   Verified 2026-08-02. Source for the dependency cycle description, the
   degenerate visitor base class, the per-element abstract visitor interfaces,
   the cross-cast dispatch, the partial visitation benefit, the recommendation to
   prefer the variant when the element hierarchy is frequently extended, and the
   listed costs including cast expense and class proliferation.
4. Philip Wadler. "The Expression Problem". Email to the Java Genericity mailing
   list, 12 November 1998.
   https://homepages.inf.ed.ac.uk/wadler/papers/expression/expression.txt
   Verified 2026-08-02. Source for the statement of the problem, defining a
   datatype by cases where one can add new cases and new functions without
   recompiling existing code and while retaining static type safety, and for
   Wadler's own note that it is a new name for an old problem discussed earlier by
   Reynolds, Cook, and Krishnamurthi, Felleisen and Friedman.
5. Oracle. *Java SE 21 API Specification*, `java.nio.file.FileVisitor`.
   https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/nio/file/FileVisitor.html
   Verified 2026-08-02. Source for the four visit operations, the
   `FileVisitResult` return values, and the `Files.walkFileTree` production use.
6. Oracle. *Java Language Updates, Java SE 21*, "Pattern Matching for switch".
   https://docs.oracle.com/en/java/javase/21/language/pattern-matching-switch.html
   Verified 2026-08-02. Source for sealed-class type coverage removing the need
   for a `default` label, and for the requirement that switch blocks using pattern
   labels be exhaustive.
7. LLVM Project. *Clang documentation*, "How to write RecursiveASTVisitor based
   ASTFrontendActions". https://clang.llvm.org/docs/RAVFrontendAction.html
   Verified 2026-08-02. Source for the `bool VisitNodeType(NodeType *)` hook form
   and the `TypeLoc` exception.
8. Python Software Foundation. *Python 3 documentation*, `ast` module,
   `ast.NodeVisitor` and `ast.NodeTransformer`.
   https://docs.python.org/3/library/ast.html
   Verified 2026-08-02. Source for the `visit_<classname>` dispatch convention,
   the `generic_visit` recursion contract, and the transformer's node replacement
   and removal semantics.
9. The Go Authors. *Go package documentation*, `go/ast`.
   https://pkg.go.dev/go/ast
   Verified 2026-08-02. Source for the `Visitor` interface declaration and the
   documented behaviour of `Walk`, including the `w.Visit(nil)` subtree-exit call.
10. Microsoft. *.NET API documentation*,
    `Microsoft.CodeAnalysis.CSharp.CSharpSyntaxWalker`.
    https://learn.microsoft.com/en-us/dotnet/api/microsoft.codeanalysis.csharp.csharpsyntaxwalker
    Verified 2026-08-02. Source for the Roslyn depth-first walker description and
    its relationship to `CSharpSyntaxVisitor`.
11. JetBrains. *Kotlin documentation*, "Sealed classes and interfaces".
    https://kotlinlang.org/docs/sealed-classes.html
    Verified 2026-08-02. Source for exhaustive `when` over a sealed class removing
    the need for an `else` clause.
12. The Rust Project Developers. *The Rust Programming Language*, chapter 6.2,
    "The match Control Flow Construct".
    https://doc.rust-lang.org/book/ch06-02-match.html
    Verified 2026-08-02. Source for match exhaustiveness and the
    non-exhaustive-patterns compiler error.
13. Jordan Rose. *Swift Evolution proposal SE-0192, "Handling Future Enum Cases"*.
    Status implemented, Swift 5.0.
    https://github.com/swiftlang/swift-evolution/blob/main/proposals/0192-non-exhaustive-enums.md
    Verified 2026-08-02. Source for the stated benefit of exhaustive enum
    switching in Swift.
