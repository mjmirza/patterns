---
name: Yo-yo Problem
slug: yo-yo-problem
family: 18-anti-patterns
category: Anti-Pattern
aliases: []
first_described: "Taenzer, Ganti, Podar 1989"
maturity: canonical
related: [template-method, strategy, composite, facade, mediator, god-object, extract-class, replace-inheritance-with-delegation, liskov-substitution-principle]
incompatible_with: [composition-over-inheritance]
verified: 2026-08-02
---

# Yo-yo Problem

## 1. Name, aliases, and lineage

The canonical name is the yo-yo problem. The term was coined by David
Taenzer, Murali Ganti, and Sudhakar Podar in "Problems in Object-Oriented
Software Reuse," a paper presented at the 1989 European Conference on
Object-Oriented Programming (ECOOP). The paper is cited by name, venue, and
year in the Wikipedia article "Yo-yo problem," which also preserves the
authors' own description of the sensation. "Often we get the feeling of
riding a yoyo when we try to understand one of these message trees"
(Wikipedia contributors, "Yo-yo problem," verified 2026-08-02, quoting
Taenzer, Ganti, Podar 1989). The primary conference paper itself was not
independently reachable while researching this entry, so the authorship,
venue, year, and the quoted sentence are attributed through that tertiary
source rather than through a direct read of the original text, and that
limitation is stated here rather than hidden.

Unlike most entries in this catalog, this anti-pattern carries essentially
one name. Every source consulted while researching this entry, the
Wikipedia article, the discussion of composition over inheritance it links
to, and the framework documentation cited in dimension 9, uses "yo-yo
problem" and nothing else. No rival term achieved separate currency the way
God Object competes with God Class, The Blob, and Kitchen Sink Class. This
entry therefore ships with an empty aliases list rather than inventing a
synonym to fill the field. This is a judgment about the state of the
literature as checked, not a claim that no other writer has ever used a
different phrase.

The name itself is the useful part of the lineage. A yo-yo, the toy, moves
up and down a string under the player's hand without settling anywhere. The
metaphor names the READER's motion, not the code's structure. A class
hierarchy does not do anything to a program; a person following control
flow through that hierarchy is the one who bounces, opening a file, jumping
to its parent, jumping again, sometimes landing back where they started. That
distinction, between a structural property (depth) and a comprehension
property (repeated, disorienting file-switching while tracing one thread of
execution), is easy to lose and is treated as load-bearing throughout this
entry, especially in dimension 4.

The term is sometimes used loosely as a synonym for "deep inheritance" or
"spaghetti inheritance" in casual conversation. That loose usage blurs an
important distinction covered in dimension 4. a hierarchy can be deep
without producing the yo-yo sensation, and a shallow hierarchy can produce
it if the bouncing pattern (a base method calling back down into an
overridden hook, which is Template Method's own mechanism, see dimension
13) is present. This entry treats "yo-yo problem" as naming the bouncing,
not the depth, following the wording of the coining source itself, which
describes the reader's experience of "riding a yoyo," not a numeric
threshold on hierarchy depth.

## 2. Problem and context

The situation announces itself the same way every time. A developer opens a
concrete class, call it FormPanel, to answer one question. what does this
object actually do when render() is called. FormPanel's own file has no
render() method in it at all. The reader jumps up to its parent, Panel.
Panel has a hook() method, which looks promising, but hook() calls
super.hook() somewhere in its body, so the reader jumps up again, to
ScrollableContainer. ScrollableContainer overrides nothing. The reader has
spent a file-open confirming that a class contributes no information, and
must jump up again, to Container, which does have code, which itself calls
super.hook(), sending the reader up one more level to Widget, the root.
Widget's hook() method calls a second method, detail(), and here the
direction reverses. because detail() is declared virtual and Panel
overrode it, the call dispatches back DOWN, past Container, past
ScrollableContainer, landing in Panel again, four levels below where the
reader currently is. To answer one question, "what does render() do for a
FormPanel," the reader opened five files and changed direction at least
three times.

This is not a hypothetical. It is the literal shape of retained-mode GUI
component hierarchies, and dimension 9 names four real, independently
documented toolkits whose public class hierarchies have exactly this shape.
a base widget class (Component, CWnd, QWidget, Widget) that declares
behavior in terms of hooks, a chain of intermediate classes that each
specialize one axis (event handling, scrolling, layout, docking), and a
concrete leaf that the application actually instantiates. The context that
produces the problem has three necessary ingredients, and removing any one
of them removes the bounce even if the class count stays the same.

- A hierarchy with enough levels that the reader cannot hold the whole
  chain in view at once. In practice this means more than two or three
  levels between the concrete class and the class that actually contains
  the behavior in question, though the exact number is less important than
  whether the reader's editor, code review tool, or terminal shows more
  than one file's worth of source at a time.
- Behavior distributed across those levels through Template Method style
  hooks and super calls, rather than concentrated at one end of the chain
  (either fully in the root, which is ordinary inheritance with no
  bouncing, or fully in the leaf, which is ordinary overriding with no
  bouncing). The bouncing specifically requires MULTIPLE levels to each
  contribute a fragment, wrapped around a call to the level above or below.
- No external aid, a call hierarchy view, a maintained sequence diagram,
  or a team convention of documenting the hook contract at the root, that
  lets the reader answer the question without personally performing the
  traversal. The cost is not intrinsic to the code; it is the cost of
  RECONSTRUCTING, by hand, from source alone, an execution order the
  source's own layout does not represent.

The problem is squarely a comprehension and maintenance cost, not a
runtime one. A debugger stepping through the same FormPanel.render() call
sees the identical sequence of frames without any confusion, because the
debugger's call stack IS the sequence diagram the reader lacks in the
source. The cost this entry is about is the one paid by a person reading
cold, in a code review, in an onboarding session, or while triaging a
production bug from a stack trace with no debugger attached, none of whom
have the debugger's advantage.

## 3. Forces

- **Reuse.** Favoured, and this is precisely why the hierarchy grows in the
  first place. Each new level exists because someone genuinely wanted to
  share the level above's behavior while adding one new piece, and
  inheritance is the most direct tool a class-based language offers for
  that. The yo-yo problem is a symptom of the reuse force being pursued
  successfully and repeatedly, not of it being misused once.
- **Extensibility.** Favoured. Template Method hooks are, by design, the
  correct way for a framework to let application code specialize one step
  of an algorithm the framework still controls, and every level in the
  chain is, individually, exercising that extension point correctly. See
  the Template Method entry for the pattern in its well-behaved form.
- **Readability and traceability.** Sacrificed, and sacrificed the most
  severely of any force in this entry. Static, single-pass, top-to-bottom
  reading of one file stops working, because the order code executes in
  does not match the order it appears in across the files a reader would
  naturally open.
- **Cognitive load.** Sacrificed. The reader must hold, in working memory,
  which levels have already been visited, which override chains are still
  open, and where control will return to, essentially performing the
  compiler's own virtual dispatch resolution by hand, and doing it
  repeatedly for every new question asked of the same object.
- **Debuggability with tooling present.** Roughly neutral to favoured. A
  debugger's call stack, an editor's "find overriding methods" or "call
  hierarchy" feature, and a language server's go-to-definition all
  externalize the bounce, turning what is expensive on paper into a few
  keystrokes on screen. This is why the yo-yo problem is talked about far
  more in code review and onboarding contexts than in live debugging
  sessions.
- **Debuggability without tooling, and code review specifically.** Sacrificed
  sharply. A GitHub diff view, a printed pull request, a terminal `less`
  session, or a stack trace pasted into a chat message none of them offer a
  way to jump straight from a call site to the overridden method that
  actually runs, so the exact same code that is cheap to trace inside a
  full editor is expensive to trace anywhere that tooling is absent, which
  includes most code review.
- **Fragile Base Class exposure.** Sacrificed as the hierarchy deepens. Every
  additional level is another place where an implicit assumption about
  calling order, about which hooks are mandatory, or about what the base
  class's default does can silently break when the base changes, because
  the contract between levels usually lives in convention and comment
  rather than in the type system, discussed further in dimension 11.
- **Onboarding and team topology.** Sacrificed for a new team member and
  favoured for a maintainer of a single, well-understood level. An engineer
  who owns exactly one level of a five-level hierarchy for years develops
  an internalized map of the whole chain and stops paying the bouncing
  cost personally, while every new hire re-pays it from the beginning, which
  is one reason the problem tends to be reported by juniors and reviewers
  rather than by the original hierarchy's long-tenured authors.

No force here is invented for the sake of balance. The trade is real. the
same hierarchy that a framework's own long-term maintainers move through
without conscious effort is the one a new contributor, a code reviewer, or
an incident responder pays the full bouncing cost against, which is why
dimension 4 treats "who is reading it, and with what tooling" as part of
deciding whether the shape is a genuine problem in a given codebase.

## 4. Applicability and non-applicability

This entry is an anti-pattern, so there is no case where deliberately
building a yo-yo shaped hierarchy is a goal for a system meant to grow.
What follows instead is when the underlying shape, a multi-level hierarchy
using Template Method hooks with super calls threaded through it, is a
tolerable, acknowledged trade, and, more importantly, when a hierarchy that
LOOKS like the yo-yo problem is not actually this anti-pattern at all. The
second list is the one worth reading carefully, because misapplying this
diagnosis leads to flattening structurally sound inheritance in pursuit of
a readability metric, which is its own cost, covered in dimension 14.

When the underlying shape is a tolerable, deliberate trade.

- A framework with a small, stable, and DOCUMENTED set of extension points,
  where the framework's own authors own and version every intermediate
  level, and application code only ever opens the one leaf class it
  subclasses, never the framework's internal levels. Django's model field
  hierarchy, referenced by name in dimension 9, is close to this shape. an
  application author overriding `formfield()` reads one method's contract
  from the documentation and rarely opens `Field`'s own source.
- A GUI toolkit's own internal widget hierarchy, where the depth models a
  taxonomy (a control that scrolls, a control that also accepts text, a
  control that also has a data model) that genuinely reflects the domain
  and changes rarely, and where the toolkit ships a generated, browsable
  class hierarchy chart specifically so nobody has to reconstruct the chain
  by reading source files in an editor. Three of the four production
  toolkits named in dimension 9 do exactly this, shipping an inheritance
  chart or an "Inherited By" listing as a first-class documentation
  artifact.
- A narrow, well tested "kernel" of at most two Template Method levels
  total (one root, one override), combined with a standing team practice of
  keeping call-hierarchy tooling, or an equivalent generated sequence
  diagram, current and consulted, so the bouncing cost is paid once by
  tooling maintenance rather than repeatedly by every reader.

When the shape does not deserve the diagnosis at all.

- A hierarchy that is deep but where each level contributes a genuinely
  separate slice of business logic with no super calls threading back and
  forth, no shared method name being wrapped at multiple levels. Reading N
  files once, in a straight line, top to bottom, each one adding
  information the last did not, is ordinary reading of a layered design. The
  defining symptom of the yo-yo problem is the reversal of direction, a
  jump back DOWN through dynamic dispatch after having already jumped up,
  not the count of files opened.
- An override that calls `super.hook()` exactly once, either strictly
  first or strictly last in its own body, never wrapping code both before
  and after the call. This costs one upward jump and no return trip, which
  is the ordinary cost of reading any inherited method and does not rise to
  the level of an anti-pattern on its own.
- A genuinely complicated ALGORITHM inside a single class or a shallow,
  two-level pair of classes, with many internal function calls but no
  inheritance chain to speak of. High call-graph complexity in flat code is
  a real cost, but it is cyclomatic and structural complexity, not this
  anti-pattern, and belongs to a different entry in this catalog rather
  than being folded into "yo-yo problem" by loose analogy.
- A hierarchy that is deep on paper but effectively dead for the code path
  in question, where an intermediate class exists in the compiled artifact
  but no override chain the reader cares about is ever actually exercised
  at runtime, because it belongs to a code path abandoned mid-migration.
  That situation is better diagnosed as Lava Flow, or as ordinary dead
  code, because the runtime bouncing this entry describes never actually
  happens; only the unnecessary file-opening does, for a call that is in
  fact a straight, single-hop dispatch once traced.
- A hierarchy that correctly models an "is-a" relationship, obeys Liskov
  substitution at every level, and rarely changes. Removing structurally
  sound inheritance purely to reduce a file-open count trades a comprehension
  cost that tooling can mitigate for a duplicated-logic cost that tooling
  cannot, and is very often the worse trade. Dimension 14 treats fixing the
  OVERRIDE PATTERN, reducing wrap-around super calls and pushing shared
  sequencing to one place, as the first move, and flattening the type
  hierarchy itself as a later, more invasive step taken only once the
  pattern-level fix has been tried and found insufficient.

## 5. Structure

- **Root class.** Declares the public entry point method that a caller
  invokes, and declares one or more protected hook methods that subclasses
  are meant to override. The root usually contains what a reader expects
  to be "the" implementation, and is frequently the FIRST class a reader
  opens, on the mistaken assumption that the root is also the class where
  the answer will be found.
- **Passthrough intermediate.** A class in the chain that overrides
  nothing at all. It exists because it is a genuine, named point in the
  domain's taxonomy, for example ScrollableContainer sitting between
  Container and Panel in a widget hierarchy, but it contributes no code to
  the specific method the reader is tracing. This participant is
  responsible for a disproportionate share of the wasted motion, because
  the reader can only learn it contributes nothing AFTER opening it.
- **Wrapping intermediate.** A class that overrides a hook and calls
  `super` from somewhere in the MIDDLE of its own body, with code both
  before and after the call. Control passes through this class twice for a
  single logical operation, once on the way down into the base
  implementation and once on the way back up, which means the reader must
  return to a file they have already read, later, to see the second half.
- **Leaf class.** The concrete type actually instantiated by the caller.
  It frequently overrides little or nothing of the method being traced,
  relying entirely on inherited behavior, yet it is both where the reader's
  investigation starts (because it is the object they hold a reference to)
  and, through virtual dispatch on a different hook called from deep inside
  the root, sometimes where control unexpectedly returns.
- **Caller.** The code that invokes the single entry-point method on the
  leaf. The caller's own file is typically short, uninvolved, and entirely
  innocent of the structure behind the call; every cost this entry
  describes is paid by whoever reads the CALLEE's implementation, not by
  whoever writes the call site.

The relationships among these participants are ordinary single inheritance,
Root is extended by each intermediate in turn, and Leaf extends the last
intermediate, so nothing about the STATIC structure is unusual or wrong on
its own. What produces the anti-pattern is the DYNAMIC relationship, shown
in dimension 7, where the sequence of method calls does not follow the
inheritance arrows in one direction, but crosses them back and forth.

## 6. ASCII structure diagram

```
  +----------------------+
  |        Widget        |   render() lives here; calls hook().
  |  # hook()             |   Reading only this file answers
  |  # detail()           |   nothing about a FormPanel.
  +----------------------+
             ^
             | extends
  +----------------------+
  |       Container       |  overrides hook(), wraps super.hook()
  |  # hook()  [override]  |  with code both before and after it.
  +----------------------+
             ^
             | extends
  +--------------------------+
  |   ScrollableContainer     |  overrides nothing at all. A reader
  |   (no overriding members) |  must open this file only to learn
  +--------------------------+  that it holds no information.
             ^
             | extends
  +----------------------+
  |         Panel          |  overrides hook() AND detail().
  |  # hook()   [override]  |
  |  # detail() [override]  |
  +----------------------+
             ^
             | extends
  +----------------------+
  |       FormPanel        |  overrides nothing. render() is
  |   (no overriding members) |  called on THIS object.
  +----------------------+

  Five files exist between the object the caller holds (FormPanel)
  and the file where render()'s own body is written (Widget).
```

## 7. Dynamics

A caller holding a `FormPanel` reference calls `render()`, which resolves,
through ordinary inheritance, to `Widget.render()`, the only place it is
defined. From there, tracing what actually happens requires crossing the
five classes in dimension 6 out of source order.

```
File a reader must open    What is found there            Direction
--------------------------  ------------------------------  ---------
1  FormPanel                render() not defined here        (start)
2  Panel                    render() not defined here          up
3  ScrollableContainer      render() not defined here          up
4  Container                render() not defined here          up
5  Widget                   render() defined; calls hook()     up

   Widget.hook() is virtual. Dispatch resolves to the MOST
   derived override, which is Panel's, four levels below Widget.

6  Panel (reopened)         hook() wraps super.hook()          down
                            "Panel.hook-before" runs, then
                            control crosses back UP again
                            through the classes with no
                            override, to reach Container's
                            override.
7  Container (reopened)     hook() wraps super.hook()            up
                            "Container.hook-before" runs
8  Widget (reopened)        base hook() body runs;               up
                            calls detail(), which is ALSO
                            virtual and dispatches to the
                            most derived override.

   detail() resolves to Panel's override, four levels below
   Widget a second time.

9  Panel (reopened again)   detail() runs, appends its trace    down
                            control unwinds back up through
                            Container and Panel to let the
                            two wrapping calls finish their
                            "after" halves.
10 Container (reopened)     "Container.hook-after" runs           up
11 Panel (reopened)         "Panel.hook-after" runs                up

Runtime trace, left to right in actual execution order:

  Panel.hook-before -> Container.hook-before -> Widget.hook
    -> Panel.detail -> Container.hook-after -> Panel.hook-after

Files opened to reconstruct that six-step trace by reading alone: 5
distinct files, with Panel opened three times and Container twice,
none of them adjacent in the sequence to the file the reader started
from.
```

This is the exact trace produced by the compiled and executed code in the
Code Examples section of this entry, in three languages, so the diagram
above is not an illustration invented for the page, it is the literal
output of a program compiled and run while writing this entry.

## 8. Implementation variants

**Classical single-inheritance chain with Template Method hooks.** The
canonical shape, and the one every production example in dimension 9 uses.
one base class per intermediate level, one or more overridden hooks, super
calls threading control back up. This is the variant illustrated in
dimensions 6 and 7 and in the code examples.

**Multiple inheritance and mixin chains.** In languages that support
multiple inheritance directly, C++, or mixin composition via a linearized
method resolution order, Python, the bouncing does not stay linear. It
becomes a graph, and the reader must additionally resolve WHICH ancestor's
override actually runs before they can even start tracing, because more
than one ancestor may define the same method name. Python's C3
linearization computes a single, well defined method resolution order at
class-creation time, so the ambiguity is resolved deterministically by the
interpreter, but a human reader must still compute or look up that same
order by hand to know which `super()` call lands where, which is strictly
more work than the single-inheritance case in dimension 7. This is
judgment drawn from how C3 linearization is documented to behave, not a
claim sourced to a specific paper describing yo-yo severity in mixin-heavy
Python codebases.

**Protocol and trait default methods.** Rust's default trait methods,
Swift's protocol extensions, and Kotlin's interfaces with default
implementations reproduce a shallow, usually single-level version of the
same bounce. a default method in the trait or protocol calls a required
method the conforming type supplies, and control crosses from the
trait's own default implementation down into the concrete type exactly
once. These languages generally discourage or structurally prevent
building a multi-level CHAIN of traits or protocols the way classes allow a
chain of subclasses, so while the individual bounce exists, the anti
pattern rarely deepens past one or two hops in idiomatic code in these
languages. This is engineering judgment about typical usage in these
language communities, not a sourced claim about any specific codebase.

**Deep retained-mode GUI component hierarchies.** The dominant real world
source of this anti-pattern, and the source of every production example
named in dimension 9. a widget toolkit's base class declares layout,
painting, or event-handling hooks, and successive intermediate classes
each add one further capability, docking, scrolling, data binding, before
reaching the concrete widget an application actually places on screen.

**ORM entity inheritance mapping.** Persistence frameworks that map a class
hierarchy onto tables, single table inheritance or joined table
inheritance in a framework such as Hibernate, or Active Record style single
table inheritance, sometimes attach a lifecycle hook (a "before save" or
"after load" callback) at each level of an entity hierarchy. Debugging why
a particular concrete entity's save behaves a certain way then reproduces
the identical file-by-file bounce described in dimension 7, once per
hook name, once per level. This variant is offered as plausible and
structurally consistent with the pattern rather than as a claim tied to a
named, cited system, and is labeled as judgment for that reason.

## 9. Known production uses

**Java Swing and AWT, the `JComponent` hierarchy.** `JComponent` extends
`Container`, which itself extends `Component`, the documentation states
this explicitly. "The `JComponent` class extends the `Container` class,
which itself extends the `Component` class." Any concrete Swing widget, for
example `JButton`, adds a further level below `JComponent` through
`AbstractButton`, producing a chain of at least five classes, `Component`,
`Container`, `JComponent`, `AbstractButton`, `JButton`, between the object
an application instantiates and the class where `Component`'s own
foundational event and painting behavior is defined. Oracle, "How to Use
Various Components," The Java Tutorials, section on `JComponent`,
https://docs.oracle.com/javase/tutorial/uiswing/components/jcomponent.html
verified 2026-08-02.

**Microsoft Foundation Classes, the `CFrameWnd` hierarchy.** The MFC class
reference page for `CFrameWnd` lists its inheritance hierarchy verbatim as
`CObject`, `CCmdTarget`, `CWnd`, `CFrameWnd`, a four level chain before any
application derives its own main-window class one level further. `CWnd`
alone is documented as the base for the entire windowing subsystem, and
MFC's own published hierarchy chart exists as a separate, dedicated
document specifically because the chain is too deep to hold in view from
any single class's reference page. Microsoft, "CFrameWnd Class," MFC
Reference documentation,
https://learn.microsoft.com/en-us/cpp/mfc/reference/cframewnd-class
verified 2026-08-02. See also Microsoft, "MFC class hierarchy chart,"
https://learn.microsoft.com/en-us/cpp/mfc/hierarchy-chart verified
2026-08-02.

**Qt, the `QAbstractSpinBox` hierarchy.** The Qt 6 reference documentation
for `QAbstractSpinBox` states its inheritance as `QObject`, `QWidget`,
`QAbstractSpinBox`, and separately lists an "Inherited By" section naming
three further concrete widgets that extend it one level deeper,
`QDateTimeEdit`, `QDoubleSpinBox`, and `QSpinBox`. A reader tracing a bug
in the spin arrows of a `QSpinBox` therefore crosses at minimum four
classes across the boundary between Qt's own C++ implementation and the
concrete widget an application uses. The Qt Company, "QAbstractSpinBox
Class," Qt 6 Reference Documentation,
https://doc.qt.io/qt-6/qabstractspinbox.html verified 2026-08-02.

**Eclipse SWT, the `Scrollable` hierarchy.** The Eclipse Platform API
reference for `org.eclipse.swt.widgets.Scrollable` documents its full
inheritance chain as `java.lang.Object`, `Widget`, `Control`, `Scrollable`,
and lists `Composite`, `List`, and `Text` as direct known subclasses one
level further, with `Composite` itself further subclassed by container
widgets such as `Group` and `Canvas` in the same package. Eclipse
Foundation, "Interface Scrollable," Eclipse Platform API,
https://help.eclipse.org/latest/topic/org.eclipse.platform.doc.isv/reference/api/org/eclipse/swt/widgets/Scrollable.html
verified 2026-08-02.

All four named systems share the same structural profile that dimension 2
describes as necessary for the anti-pattern. a base class, `Component`,
`CWnd`, `QWidget`, or `Widget`, that declares behavior through overridable
hooks, several intermediate levels each responsible for one orthogonal
capability, and a concrete leaf an application actually uses. Three of the
four, MFC, Qt, and SWT, mitigate the reading cost precisely the way
dimension 4 describes as the tolerable case, by publishing a dedicated,
generated hierarchy chart or an explicit "Inherited By" listing as part of
their reference documentation, rather than leaving readers to reconstruct
the chain from source alone.

## 10. Consequences

Positive, from the underlying design intent, Template Method style reuse
and extensibility, when the hierarchy stays within the tolerable bound
described in dimension 4.

- Behavior genuinely shared across many concrete leaf classes is written
  once, in the appropriate ancestor, rather than duplicated at every leaf.
- New concrete variants are added by writing a small subclass that
  overrides only the hooks it needs to change, leaving the rest of a
  well-tested algorithm untouched.
- A framework can expose a small number of documented extension points
  while keeping full control of the surrounding sequencing, which is the
  entire value proposition of Template Method, covered in dimension 13.

Negative, once the hierarchy passes the point described in dimension 4 and
the bouncing pattern is present.

- A single question about runtime behavior, answerable in one file in a
  flat design, now costs several file switches and a change of direction,
  as measured concretely in dimension 7.
- Code review quality degrades, because reviewers working from a diff view
  cannot see the intermediate levels a change interacts with unless they
  separately open the whole ancestor chain, which most review tools do not
  surface automatically.
- Onboarding time increases for any engineer who did not personally build
  the hierarchy, because the map of which level does what is held in the
  original authors' memory rather than in a form a newcomer can consult.
- The base class becomes fragile, in the sense described by the Fragile
  Base Class problem and elaborated in dimension 11, because an implicit
  contract, call order, mandatory super calls, which hooks are optional,
  lives in convention rather than in the type system, and a change at one
  level can silently break a distant, unrelated-looking override.
- Debugging without a debugger, from a stack trace pasted into an incident
  channel, or from a log line with no attached interactive session,
  becomes disproportionately harder, because the aid that makes the
  bouncing cheap, a call hierarchy view or a live call stack, is exactly
  the aid that is unavailable in those situations.

## 11. Failure modes and misuse

**The forgotten super call.** Symptom. A feature that was meant to extend
the base behavior is only partially present at runtime, with no exception
and no compile error, because the reader who wrote the override forgot to
call `super.hook()`. Cause. The obligation to call super lives only in
convention or in a comment at the base class, invisible from the
overriding class's own file. Fix. Restructure the base class so it controls
sequencing directly and calls small, separately overridable primitive
operations, the textbook Template Method shape, so no subclass is ever
responsible for remembering to invoke a base implementation; where that
restructuring is not immediately possible, add a test asserting each
concrete leaf exhibits the base behavior, matching the type-assertion test
described for a related pattern in the Factory Method entry, dimension 15.

**The duplicated side effect.** Symptom. A resource, a listener
registration, a database row, is created or fired twice for what looks
like a single logical operation, discovered as a duplicate row bug or an
event handler firing twice. Cause. Two different levels of the hierarchy
each independently call the same shared setup logic, one directly and one
through an unrelated-looking super call further up the chain, so the
duplication is invisible from either call site in isolation. Fix. Make the
setup logic idempotent, or, better, move it to a single point in the chain
that every leaf reaches exactly once regardless of which hooks it
overrides, which usually means moving it out of an overridable hook
entirely and into a `final` or otherwise non-overridable method on the
root.

**Reaching for a debugger to read straightforward code.** Symptom.
Engineers routinely set a breakpoint and single-step through a call that
has no actual runtime complexity, purely because reading the source in an
editor or a code review tool does not reveal the execution order. Cause.
The bouncing cost from dimension 3 has been silently pushed from static
reading time onto interactive debugging time, which doubles as a signal
that the hierarchy has crossed the tolerable line described in dimension
4. Fix. Generate and maintain a call-hierarchy artifact, a sequence diagram
in the style of dimension 7, or a documented hook contract at the root
class, so the debugger stops being the only place the sequence is visible.

**Concurrent edits at different levels colliding silently.** Symptom. Two
independently reviewed and independently correct-looking changes, one
editing `Container.hook()`, the other editing `Panel.hook()`, combine at
runtime into a bug that neither change's own review caught, because no
single review traced the combined effect across both files. Cause. Several
files share one logical method name and one control-flow thread, with no
single file acting as the owner of the whole sequence. Fix. Assign a
single owning file, typically the root class, as the place the FULL
sequence is documented and reviewed whenever any level in the chain
changes, and require that review even when the diff itself is entirely
within one intermediate class.

**Fragile base class breakage from reordering.** Symptom. An apparently
safe change to the base class, reordering two statements inside its hook
method, silently breaks a leaf class three levels down whose override
depended on the OLD order, discovered only when that specific leaf's
behavior regresses in production. Cause. The dependency between the base
class's internal ordering and a distant subclass's assumptions is
implicit, present in neither file's text, and therefore invisible to a
reviewer of either change in isolation. This is the general Fragile Base
Class problem, and the yo-yo shape is exactly the structure in which it
tends to occur, because the base class's sequencing and the subclass's
expectations are separated by the same distance a reader must bounce
across. Fix. State the hook contract explicitly, in documentation attached
to the root class, and where the language allows it, make the outer
algorithm method non-overridable so subclasses cannot silently depend on
an ordering they do not actually control.

**The empty intermediate class trap.** Symptom. A reader tracing a bug
opens an intermediate class purely to confirm it contributes nothing to
the method in question, having had no way to know that in advance, wasting
a file open for zero information. Cause. The hierarchy accumulated one
level per historical specialization and was never pruned once a level
stopped contributing distinct behavior to the method being traced. Fix.
Collapse the empty intermediate using the Inline Class refactoring,
described in general terms in dimension 14, once it is confirmed the
intermediate genuinely contributes nothing across the methods that matter,
not only the one the reader happened to be tracing.

## 12. Trade-off matrix

Compared against named alternatives across the forces from dimension 3. the
deep Template Method chain that produces the yo-yo problem, a shallow
two-level Template Method (the tolerable case from dimension 4), Strategy
substituting an injected object for the hook, Decorator wrapping behavior
at runtime instead of at compile time through subclassing, and a flat
ordered pipeline of named steps, the shape used in dimension 14's
refactoring path and in this entry's own code examples.

| Force | Deep Template Method chain (yo-yo shape) | Shallow Template Method (one override level) | Strategy | Decorator | Flat step pipeline |
|---|---|---|---|---|---|
| Reuse of shared logic | High, that is why it grew | High | High, via the shared interface | High, via wrapping | High, shared steps composed by reference |
| Files to trace one call, cold read | Many, direction reverses | One or two, direction is mostly one way | One or two, no reversal | Proportional to wrap depth, but explicit at the composition site | One, the pipeline definition itself |
| Extensibility for a new variant | New subclass, cheap to add, cheap to misuse | New subclass, same trade at smaller scale | New strategy implementation, no subclass | New decorator, no subclass | New step function, no subclass |
| Debuggability without an editor or debugger | Poor | Fair | Good | Fair, wrapping order must still be found | Good, order is the list order |
| Fragile Base Class exposure | High | Low to moderate | Low, no shared implicit sequencing | Moderate, wrap order still implicit at the call site | Low, order is an explicit, inspectable list |
| Cost to add cross-cutting ordering change | Edit the base, ripples through every override's assumptions | Edit the base, ripples through the one override | Edit the composition, no ripple into strategy implementations | Reorder the wrap chain at the composition site | Reorder the list, no code change inside any step |
| Where the "table of contents" lives | Nowhere, unless separately documented | Small enough to often not need one | The composition root | The composition root | The pipeline definition itself |

Reading of the table. The deep chain wins on nothing except that it was the
path of least resistance for whoever added the fifth level, having already
had four. Every other named alternative preserves the genuine reuse the
chain was built for while keeping the "what runs, in what order" question
answerable from a single place, which is the property the yo-yo problem's
victims are actually missing.

## 13. Related and incompatible patterns

- **Template Method.** The mechanism, not the anti-pattern. The yo-yo
  problem is what Template Method degenerates into once it is nested more
  than roughly two levels deep with several hooks and wrap-around super
  calls at more than one level. A shallow, disciplined Template Method, one
  root, one override, a documented hook contract, is not this anti-pattern
  and remains the correct tool for the extensibility force named in
  dimension 3.
- **Strategy.** A substitute for the shared hook, addressing the root
  cause directly. Where Template Method varies one step of an algorithm by
  subclassing the class that runs the algorithm, Strategy varies the same
  step by injecting a separate object that implements a narrow interface,
  which removes the inheritance chain, and with it the reversal of
  direction, entirely. The fixed code examples in this entry use a shape
  closely related to Strategy, a list of independent, composable steps.
- **Composite.** Frequently confused with this anti-pattern because
  Composite trees are also described as "deep," but the two kinds of depth
  are different. Composite's depth is a runtime OBJECT graph, potentially
  many instances of a small, fixed number of classes, read by opening one
  or two class files once, regardless of how many objects the tree
  contains at runtime. The yo-yo problem's depth is a compile-time CLASS
  chain, where every additional level is an additional file a reader must
  personally open, no matter how many or how few objects exist at runtime.
  A deep Composite tree of a thousand nodes at three classes is cheaper to
  read than a five-class Template Method chain instantiated once.
- **Facade.** Mitigates the symptom for CALLERS of the deep hierarchy
  without removing the underlying structure. A Facade placed in front of a
  yo-yo shaped subsystem lets external code avoid tracing the chain
  entirely, but the cost this entry describes is still paid in full by
  whoever maintains the subsystem behind the facade.
- **Mediator.** Addresses the root cause the same way Strategy does, by
  relocating cross-object coordination that would otherwise be threaded
  through a chain of super calls into one dedicated object, so the
  sequencing question has a single, named home instead of being implicit
  across several levels.
- **God Object.** The opposite failure mode on the same underlying axis.
  Where the yo-yo problem scatters one behavior thinly across too many
  classes, God Object concentrates too many unrelated behaviors into too
  few. Both are readability and maintainability anti-patterns pointed in
  opposite directions, and over-correcting one by collapsing an entire
  hierarchy into a single class without separating genuinely distinct
  responsibilities risks landing directly on the other, which is the case
  dimension 14's caution about flattening structurally sound inheritance
  is aimed at.
- **Refused Bequest.** Frequently co-occurs in the same hierarchies. a
  chain built for reuse tends to produce subclasses partway down that only
  want SOME of what an ancestor offers, which is a related but distinct
  smell about the CONTENT of what is inherited rather than about the
  reading cost of tracing it.
- **Liskov Substitution Principle.** A hierarchy that violates
  substitutability is a stronger signal that the type structure itself is
  wrong and should be reconsidered, whereas a hierarchy that fully obeys it
  but still produces the yo-yo problem has a sound type structure and a
  purely mechanical bouncing problem in HOW behavior is threaded through
  that structure, the distinction dimension 4's non-applicability list
  relies on.

## 14. Refactoring path in and out

Introducing the shape is, unfortunately, the easy and common direction, and
usually happens by accretion rather than by decision. a team adds one
subclass to specialize one axis, then a second team adds another subclass
on top of the first to specialize a different axis, and the chain grows one
well-intentioned level at a time with no single decision point at which
anyone chose to build a five-level hierarchy on purpose. Recognizing that
accretion pattern early, and treating each new subclass-of-a-subclass as a
moment to ask whether the new specialization could instead be a Strategy or
a composed step rather than one more inheritance level, is the cheapest
prevention available, and it is prevention rather than a refactor, because
once the chain exists the removal is materially more invasive than the
addition ever was.

Removing the anti-pattern once it is present, in increasing order of
invasiveness, matching the caution in dimension 4 about not skipping
straight to flattening a sound type hierarchy.

1. **Tighten the hook contract before touching the hierarchy's shape.**
   Confirm which hooks genuinely need to be overridable and which have
   settled, in practice, to a single behavior across every leaf. Where a
   hook has one real implementation left, inline it into the base class and
   remove the override point, shrinking the number of files a reader must
   visit without changing the class hierarchy itself.
2. **Make the outer sequencing non-overridable.** Where the language
   supports it, mark the entry-point method `final`, `sealed`, or its
   equivalent, so the ORDER hooks run in is guaranteed by the base class
   alone and can never be silently altered by an intermediate level's own
   super-call placement. This does not remove any files from the chain, but
   it removes the reversal-of-direction risk described in dimension 11's
   fragile base class failure mode, because the order becomes provably
   fixed rather than dependent on how each override happens to call super.
3. **Collapse passthrough intermediates.** For every class in the chain
   that overrides nothing relevant to the method being traced, confirmed
   across every method that matters, not only the one under investigation,
   apply Inline Class, folding the passthrough level directly into its
   child, removing one stop from every future trace.
4. **Extract the varying step into an injected collaborator.** Take the
   single hook that genuinely differs across leaf classes and replace it
   with a constructor-supplied object or function implementing a narrow,
   named interface, the shape used throughout this entry's fixed code
   examples. Each existing leaf subclass becomes a call site that supplies
   its own small implementation of that one interface, rather than a
   subclass carrying the whole inherited weight of the chain above it.
5. **Flatten the remaining chain into one class parameterized by
   composition.** Once step 4 has moved the varying behavior out of the
   type hierarchy, the intermediate classes that remain typically have no
   further reason to exist as separate types, since their only purpose was
   to route control through the correct sequence of hooks, which a single
   class holding an ordered list of steps now does directly and visibly, as
   shown in dimension 7's fixed shape. Delete the now-redundant subclasses.
6. **Add a regression test asserting the full sequence.** Before deleting
   any class in step 5, add a test that runs the ORIGINAL hierarchy end to
   end and records the exact sequence of side effects it produces, matching
   the style of the trace captured in dimension 7. Run the same test
   against the flattened replacement and confirm the sequence is identical,
   so the refactor is proven behavior-preserving rather than merely
   assumed to be.

The reverse direction, reintroducing a Template Method chain into flat,
composed code, is occasionally the right move when a genuine, stable,
externally-owned extension point is needed, described in dimension 4's
tolerable-case list, and follows the same steps run backward. name the
single method that must vary, express it as an abstract method on a new
base class, and migrate callers of the composed version to subclasses one
at a time, stopping deliberately once the hierarchy reaches the depth
dimension 4 treats as acceptable rather than continuing to add levels by
habit.

## 15. Testing and verification

Harder because of the anti-pattern.

- A unit test that exercises one leaf class must, in effect, also exercise
  every intermediate level's hook implementation, whether or not the test
  author is aware those levels exist, because dynamic dispatch runs all of
  them regardless of which file the test author had open while writing the
  assertion.
- A change to the shared sequencing at the root class has a genuinely large
  blast radius, potentially every leaf across the whole hierarchy, but the
  existing test suite frequently does not make that blast radius visible,
  because tests are usually organized per leaf class rather than per shared
  hook, so a base-class regression can pass every existing per-leaf test
  individually while still breaking an interaction between two hooks that
  no single test exercises together.
- Mocking or stubbing one level in isolation, to unit test a single
  intermediate class's contribution without running the whole chain, is
  awkward in most mocking frameworks, because the method under test calls
  `super`, and a partial mock of the class under test does not, in
  general, give the test author control over what that specific super call
  does.

Easier once the flattened, composed shape from dimension 14 is in place.

- Each step in the flattened pipeline is a small, independently
  constructible unit, function, closure, or narrow-interface object, that
  can be unit tested in complete isolation, with no hierarchy, no
  `super`, and no dynamic dispatch to reason about.
- The full sequence a caller experiences is testable directly, by
  constructing the pipeline with a known list of steps and asserting the
  recorded order of side effects, exactly as the code examples in this
  entry do, rather than being reconstructed indirectly through the
  behavior of a chain of subclasses.

Techniques that apply directly to code still in the yo-yo shape, before a
refactor is undertaken.

- **The trace-capturing regression test**, illustrated in dimension 14 step
  6 and implemented literally in the code examples below, records the
  exact ordered sequence of side effects a concrete leaf produces. This is
  the single most useful test to write BEFORE attempting any of the
  refactoring steps in dimension 14, because it is the test that proves
  each subsequent step preserved behavior.
- **A type-assertion test per leaf**, adapted from the same technique
  described in the Factory Method entry, dimension 15, confirms every
  concrete class in the hierarchy still produces the runtime type its
  ancestors expect, catching the forgotten-super-call failure mode from
  dimension 11 at build time rather than in production.
- **A documented, testable hook contract.** Where the hierarchy cannot be
  flattened immediately, writing one shared, abstract test case against
  the ROOT class's hook contract, then running it once per concrete leaf,
  the same contract-test technique used for Factory Method's Product
  interface, at minimum confirms every leaf honors the sequencing the base
  class assumes, even while the file-tracing cost described throughout
  this entry remains present for a human reader.

## 16. Observability signals

The anti-pattern is, by nature, a static reading cost rather than a
runtime failure, so it leaves few direct traces in production telemetry on
its own. What is genuinely observable are the downstream failure modes
from dimension 11, and the process signals a team can track to notice the
underlying shape is becoming a real cost.

What to record and watch.

- Code review turnaround time, and specifically reviewer comment counts,
  on pull requests that touch any single level of a known deep hierarchy.
  a rising trend, particularly comments asking "where does this actually
  get called," is a direct, human generated signal that the bouncing cost
  from dimension 3 has crossed from tolerable to expensive for this
  specific team.
- Incident postmortems that name a "silently missing behavior" or a
  "duplicate side effect" root cause, matching the first two failure modes
  in dimension 11, are worth tagging when the affected code sits inside a
  multi-level inheritance chain, so a recurring pattern across otherwise
  unrelated incidents becomes visible over time.
- Time-to-first-meaningful-contribution for new engineers assigned to a
  codebase area built around a known deep hierarchy, tracked the same way a
  team already tracks general onboarding metrics, isolating that one area
  as an outlier is a slow but reliable signal.
- Static analysis of maximum inheritance depth per class, a metric most
  mainstream linters and code-quality tools already compute, is not itself
  proof of the anti-pattern, per the non-applicability list in dimension
  4, but a rising trend in that metric combined with the qualitative
  review-friction signal above is worth treating as a joint indicator
  rather than either signal read in isolation.

A healthy state looks like a flat or declining trend on all of the above,
paired with a maintained call-hierarchy artifact or an equivalent tool
being actively used, matching the tolerable case from dimension 4. A
degrading state looks like the review-friction and incident-tagging
signals both rising together on the same subsystem, with no corresponding
documentation or tooling investment keeping pace, which is the point at
which dimension 14's refactoring path is worth prioritizing rather than
deferring further.

## 17. Security and privacy implications

The anti-pattern is largely silent on security and privacy in its own
right; saying otherwise would invent a concern this shape does not
directly create. Two genuine, narrower implications follow from the
comprehension cost described throughout this entry, and are stated here
as analytical judgment rather than as sourced facts.

**Security review cost.** A security reviewer auditing a code path for an
authorization check, an input validation step, or a data-handling rule
must trace the FULL execution path to confirm the control is actually
applied, not merely present somewhere in the source tree. Where that path
crosses a yo-yo shaped hierarchy, the reviewer pays the same bouncing cost
described in dimension 3, and a control genuinely present at one level but
silently bypassed by an override at another level, the forgotten-super-call
failure mode from dimension 11 applied to a security-relevant hook rather
than a UI hook, is materially harder to spot in a hierarchy a reviewer must
reconstruct by hand than in a flat, single-file code path.

**Incident response latency.** During an active incident, an engineer
reconstructing what a specific request path did, often from logs or a
stack trace with no live debugger attached, pays the worst-case version of
the cost described in dimension 3, the debugger's usual mitigation is
specifically unavailable, which directly extends the time to root cause
for any incident whose affected code sits inside a deep hierarchy of this
shape.

On data privacy specifically, the pattern has no direct implication beyond
these two general points, and no privacy-specific claim is made here that
was not independently verifiable during the research for this entry.

## Code examples

Three languages, each showing the identical anti-pattern shape followed by
the identical fix, so the runtime trace can be compared directly across
languages. Java, TypeScript, and Python are chosen because each supports
classical single-inheritance dispatch with an explicit `super` call, which
is the mechanism the bouncing in dimension 7 depends on. Go and Rust are
omitted from the anti-pattern side of this entry because neither language
has classical class inheritance, so the multi-level `super`-call chain this
entry is about does not translate directly; Rust's own closest analog,
default trait methods calling required trait methods, is discussed instead
as a shallower, related variant in dimension 8 rather than reproduced as a
fifth full example here.

Both blocks in every language were compiled or run while writing this
entry, and each prints the exact trace shown in dimension 7's diagram.

### Java

The anti-pattern. Five classes, a hook wrapped with `super` at two
different levels, and a second hook that dispatches back down through
virtual dispatch.

```java
abstract class Widget {
    protected StringBuilder trace = new StringBuilder();

    void render() {
        hook();
    }

    protected void hook() {
        trace.append("Widget.hook ");
        detail();
    }

    protected void detail() {
        trace.append("Widget.detail ");
    }
}

class Container extends Widget {
    @Override
    protected void hook() {
        trace.append("Container.hook-before ");
        super.hook();
        trace.append("Container.hook-after ");
    }
}

class ScrollableContainer extends Container {
}

class Panel extends ScrollableContainer {
    @Override
    protected void hook() {
        trace.append("Panel.hook-before ");
        super.hook();
        trace.append("Panel.hook-after ");
    }

    @Override
    protected void detail() {
        trace.append("Panel.detail ");
    }
}

class FormPanel extends Panel {
}

public class YoYoDemo {
    public static void main(String[] args) {
        FormPanel form = new FormPanel();
        form.render();
        System.out.println(form.trace.toString().trim());
    }
}
```

Running the demo prints exactly the sequence traced by hand in dimension
7. `Panel.hook-before Container.hook-before Widget.hook Panel.detail
Container.hook-after Panel.hook-after`, confirming that the five classes
above are opened, and two of them reopened, to account for a six-step
sequence.

The fix, dimension 14 steps 4 and 5 applied. one class, no inheritance, an
ordered list of small, independently testable steps supplied at
construction time.

```java
import java.util.List;
import java.util.function.Consumer;

final class Widget {
    private final List<Consumer<List<String>>> steps;
    private final List<String> trace = new java.util.ArrayList<>();

    Widget(List<Consumer<List<String>>> steps) {
        this.steps = steps;
    }

    void render() {
        for (Consumer<List<String>> step : steps) {
            step.accept(trace);
        }
    }

    List<String> trace() {
        return trace;
    }

    public static void main(String[] args) {
        Consumer<List<String>> beforeScroll = t -> t.add("before-scroll-clip");
        Consumer<List<String>> panelFields = t -> t.add("panel-fields");
        Consumer<List<String>> afterScroll = t -> t.add("after-scroll-clip");

        Widget form = new Widget(List.of(beforeScroll, panelFields, afterScroll));
        form.render();
        System.out.println(String.join(" ", form.trace()));
    }
}
```

Reading `render()` alone now answers the "what runs, in what order"
question completely, in one file, with no class to jump to.

### TypeScript

The identical shape, and the identical trace, in a second language.

```typescript
abstract class Widget {
  trace: string[] = [];

  render(): void {
    this.hook();
  }

  protected hook(): void {
    this.trace.push("Widget.hook");
    this.detail();
  }

  protected detail(): void {
    this.trace.push("Widget.detail");
  }
}

class Container extends Widget {
  protected override hook(): void {
    this.trace.push("Container.hook-before");
    super.hook();
    this.trace.push("Container.hook-after");
  }
}

class ScrollableContainer extends Container {
}

class Panel extends ScrollableContainer {
  protected override hook(): void {
    this.trace.push("Panel.hook-before");
    super.hook();
    this.trace.push("Panel.hook-after");
  }

  protected override detail(): void {
    this.trace.push("Panel.detail");
  }
}

class FormPanel extends Panel {
}

const form = new FormPanel();
form.render();
console.log(form.trace.join(" "));
```

The fix, the same ordered-step shape as the Java version, showing the
pattern is not language specific.

```typescript
type Step = (trace: string[]) => void;

class Widget {
  trace: string[] = [];
  constructor(private steps: Step[]) {}

  render(): void {
    for (const step of this.steps) step(this.trace);
  }
}

const beforeScroll: Step = (t) => t.push("before-scroll-clip");
const panelFields: Step = (t) => t.push("panel-fields");
const afterScroll: Step = (t) => t.push("after-scroll-clip");

const form = new Widget([beforeScroll, panelFields, afterScroll]);
form.render();
console.log(form.trace.join(" "));
```

### Python

The same shape a third time, using `super()` the way Python idiomatically
expresses it, and demonstrating that the bouncing is a property of the
override pattern, not of any one language's specific inheritance syntax.

```python
class Widget:
    def __init__(self) -> None:
        self.trace: list[str] = []

    def render(self) -> None:
        self.hook()

    def hook(self) -> None:
        self.trace.append("Widget.hook")
        self.detail()

    def detail(self) -> None:
        self.trace.append("Widget.detail")


class Container(Widget):
    def hook(self) -> None:
        self.trace.append("Container.hook-before")
        super().hook()
        self.trace.append("Container.hook-after")


class ScrollableContainer(Container):
    pass


class Panel(ScrollableContainer):
    def hook(self) -> None:
        self.trace.append("Panel.hook-before")
        super().hook()
        self.trace.append("Panel.hook-after")

    def detail(self) -> None:
        self.trace.append("Panel.detail")


class FormPanel(Panel):
    pass


if __name__ == "__main__":
    form = FormPanel()
    form.render()
    print(" ".join(form.trace))
```

The fix, the same ordered list of independent callables, this time using
plain functions rather than an interface, which is the idiomatic Python
form of the same refactor.

```python
from typing import Callable

Step = Callable[[list[str]], None]


class Widget:
    def __init__(self, steps: list[Step]) -> None:
        self.steps = steps
        self.trace: list[str] = []

    def render(self) -> None:
        for step in self.steps:
            step(self.trace)


def before_scroll(trace: list[str]) -> None:
    trace.append("before-scroll-clip")


def panel_fields(trace: list[str]) -> None:
    trace.append("panel-fields")


def after_scroll(trace: list[str]) -> None:
    trace.append("after-scroll-clip")


if __name__ == "__main__":
    form = Widget([before_scroll, panel_fields, after_scroll])
    form.render()
    print(" ".join(form.trace))
```

## 18. References

1. Taenzer, David, Murali Ganti, and Sudhakar Podar. "Problems in
   Object-Oriented Software Reuse." Presented at the European Conference on
   Object-Oriented Programming (ECOOP), 1989. Source of the coined term and
   the "riding a yoyo" quotation, attributed through the Wikipedia article
   below because the primary conference paper was not independently
   reachable during research for this entry.
2. Wikipedia contributors. "Yo-yo problem."
   https://en.wikipedia.org/wiki/Yo-yo_problem verified 2026-08-02. Source
   for the coining attribution, the year, the venue, the direct quotation
   in dimension 1, and the general mitigation guidance summarized in
   dimensions 1 and 2.
3. Wikipedia contributors. "Composition over inheritance."
   https://en.wikipedia.org/wiki/Composition_over_inheritance verified
   2026-08-02. Source for the general framing that composition avoids
   problems associated with deep, multi-generation inheritance models,
   itself citing Eric Freeman, Elisabeth Robson, Bert Bates, and Kathy
   Sierra, Head First Design Patterns, O'Reilly Media, 2004.
4. Oracle. "How to Use Various Components," The Java Tutorials, section on
   `JComponent`.
   https://docs.oracle.com/javase/tutorial/uiswing/components/jcomponent.html
   verified 2026-08-02. Source for the Java Swing `JComponent` production
   use in dimension 9.
5. Microsoft. "CFrameWnd Class," MFC Reference documentation.
   https://learn.microsoft.com/en-us/cpp/mfc/reference/cframewnd-class
   verified 2026-08-02. Source for the MFC `CFrameWnd` inheritance
   hierarchy quoted in dimension 9.
6. Microsoft. "MFC class hierarchy chart."
   https://learn.microsoft.com/en-us/cpp/mfc/hierarchy-chart verified
   2026-08-02. Source for MFC's dedicated hierarchy-chart documentation
   artifact, cited as the tolerable-case mitigation example in dimensions
   4 and 9.
7. The Qt Company. "QAbstractSpinBox Class," Qt 6 Reference Documentation.
   https://doc.qt.io/qt-6/qabstractspinbox.html verified 2026-08-02.
   Source for the Qt widget hierarchy and "Inherited By" listing cited in
   dimension 9.
8. Eclipse Foundation. "Interface Scrollable," Eclipse Platform API.
   https://help.eclipse.org/latest/topic/org.eclipse.platform.doc.isv/reference/api/org/eclipse/swt/widgets/Scrollable.html
   verified 2026-08-02. Source for the Eclipse SWT `Scrollable` inheritance
   hierarchy and its documented subclasses cited in dimension 9.
