---
name: Flyweight
slug: flyweight
family: 01-design-patterns-gof
category: Structural
aliases: [Glyph, Interning, Hash Consing, Canonicalization, Shared Immutable Value]
first_described: "Calder and Linton 1990, cataloged by Gamma, Helm, Johnson, Vlissides 1994"
maturity: canonical
related: [factory-method, composite, singleton, prototype, proxy, object-pool, memoization, value-object]
incompatible_with: [mutable-shared-state]
verified: 2026-08-02
---

# Flyweight

## 1. Name, aliases, and lineage

The canonical name is Flyweight. It sits in the Gang of Four catalog among the
seven structural patterns, in Erich Gamma, Richard Helm, Ralph Johnson and John
Vlissides, *Design Patterns. Elements of Reusable Object-Oriented Software*,
Addison-Wesley, 1994, chapter 4, Structural Patterns, section Flyweight. The
catalog describes the pattern as using sharing to support large numbers of
fine-grained objects efficiently, and the whole design turns on splitting an
object's state into a shareable part and a non-shareable part
([Wikipedia summary of the pattern and its state split](https://en.wikipedia.org/wiki/Flyweight_pattern),
verified 2026-08-02).

The name and the technique predate the catalog. Paul R. Calder and Mark A.
Linton published "Glyphs: flyweight objects for user interfaces" at the third
ACM SIGGRAPH symposium on User Interface Software and Technology in 1990, pages
92 to 101, DOI 10.1145/97924.97935
([dblp bibliographic record](https://dblp.uni-trier.de/rec/conf/uist/CalderL90.html),
verified 2026-08-02). Their paper defines small components called glyphs meant
to be created in very large numbers, and demonstrates them by building a WYSIWYG
document editor out of them. The GoF book's document editor running example, the
one where every character in a document is an object, comes directly out of that
lineage. Wikipedia records the same attribution, that the concept was coined and
first explored by Calder and Linton in 1990 to handle glyph information in a
WYSIWYG editor
([Wikipedia](https://en.wikipedia.org/wiki/Flyweight_pattern), verified
2026-08-02). Anyone reading the pattern purely as a memory trick is reading only
half of it. The other half is the observation that a fine-grained object model,
one object per character rather than one object per paragraph, becomes
affordable once identical objects are shared.

Several names in wide use describe the same idea from different communities, and
knowing which one a colleague means saves an argument.

- **Interning.** The runtime or standard library name for Flyweight applied to a
  single canonical type, usually strings or boxed integers. Java, .NET, Python,
  and Ruby all ship an interning facility. The pool is process-wide, the products
  are immutable, and the lookup key is the value itself.
- **Hash consing.** The functional programming and compiler community's name for
  the same operation applied to immutable tree nodes, so that two equal subtrees
  become pointer-equal. It carries an extra promise beyond interning, namely that
  structural equality collapses to pointer equality, which turns a deep
  comparison into one machine instruction.
- **Canonicalization.** The term used in symbol tables, in XML and DOM
  implementations, and in ontology tooling, for mapping many equal representations
  to one representative instance.
- **Glyph.** The original Calder and Linton name, still used inside text layout
  and rendering engines for the shared, position-free character object.
- **Instancing.** The graphics community's name for the same split, where the
  shared mesh and textures are the intrinsic part and a per-instance transform
  matrix is the extrinsic part. See dimension 9 for the Unreal Engine numbers.

A useful separator against neighbouring ideas. If the shared object carries the
context-dependent data, it is not a flyweight, it is a cache. If the object is
handed out to exactly one caller at a time and returned afterwards, it is not a
flyweight, it is an object pool. Flyweight objects are shared concurrently, by
many holders, forever, and that is only sound because they carry no state that
any holder could disagree about.

## 2. Problem and context

A program needs a very large number of objects that are almost all the same,
and the memory cost of representing each one separately is what is going to
break it.

The situation reads like this in a real codebase. A model starts small. A
document is a list of characters, each character an object holding its
codepoint, its font family, its point size, its weight, its colour, and its
position. That model is a pleasure to write algorithms against, because
everything is uniform and every operation is a loop over objects. Then a
customer opens a two hundred page document. There are now four hundred thousand
character objects, each carrying a font family string pointer, a size, a weight,
a colour, plus per-object allocation overhead and a header. On a runtime with a
sixteen byte object header, four hundred thousand objects cost several megabytes
before any field is counted, and the font family string is duplicated four
hundred thousand times even though the document uses three fonts.

The same shape appears far from text.

- A tile map in a game, where a hundred thousand tiles each hold a full copy of
  the terrain description: movement cost, texture handle, footstep sound, walk
  speed. The map uses eight distinct terrains.
- A column-oriented analytics table holding fifty million rows, where a string
  column has only forty distinct values.
- A parsed abstract syntax tree where the same identifier name appears in ten
  thousand places, allocated ten thousand times.
- A network of graph nodes where every node holds a reference to a shared
  configuration object that was constructed once per node instead of once.
- A rendering scene with fifty thousand trees, each holding a full copy of the
  mesh vertices.

The observation that makes Flyweight work is that these objects are not actually
all different. Split the fields into two groups.

- **Intrinsic state.** The fields whose values are shared by many objects and do
  not depend on where the object appears. Font family, point size, weight. The
  terrain's movement cost and texture. The tree's mesh and textures. The string's
  characters. Intrinsic state is context-independent, so one instance can stand
  in for every object that carries the same values.
- **Extrinsic state.** The fields that differ per occurrence and depend on
  context. The character's x and y position on the page. The tile's row and
  column. The tree's world transform. Extrinsic state cannot be shared, because
  by definition every holder has a different value for it.

The pattern removes the intrinsic state from the per-object storage and shares it
through a pool, and it either stores the extrinsic state in the container or
passes it in as a parameter at every call. The four hundred thousand character
objects collapse into four hundred thousand small position records plus three
shared style objects.

The context in which this is the right answer has four parts, and all four have
to hold.

- The object count is genuinely large, in the hundreds of thousands or more, or
  the per-object payload is genuinely heavy, such as a mesh or a rasterised
  image.
- The intrinsic state has few distinct values relative to the object count. Three
  fonts across four hundred thousand characters is the shape. Four hundred
  thousand distinct fonts is not.
- The intrinsic state is immutable, or can be made immutable without a fight.
- The extrinsic state has somewhere sensible to live, either in the container
  that walks the flyweights or computable at the call site.

Outside that context the pattern costs indirection, a lookup, and a
comprehension tax, and returns nothing. See dimension 4.

## 3. Forces

This dimension weighs pressures against each other and is engineering judgement
rather than sourced fact, except where a source is named.

- **Memory footprint.** Favoured, and this is the only force the pattern exists
  to serve. Everything else it touches, it makes worse. That asymmetry is the
  honest summary of Flyweight and it belongs at the top of any discussion of it.
- **Lookup latency.** Sacrificed. Every acquisition of a flyweight costs a hash
  of the key plus a map probe, where the naive design costs an allocation. On a
  modern allocator a small young-generation allocation is a pointer bump, and a
  hash map probe is a hash plus a cache-missing indirection. It is entirely
  possible for the flyweight version to be slower per acquisition than the
  version it replaced.
- **Access latency.** Favoured once the data set is large, and this is the part
  people forget. Once the objects are in place, a smaller working set fits in
  cache. A tile map whose per-tile record shrinks from forty-eight bytes to eight
  bytes fits six times as many tiles per cache line, and a scan over it can be
  several times faster even though each access now costs a pointer dereference.
  The memory win frequently buys a throughput win that dwarfs the lookup cost.
- **Cognitive load.** Sacrificed, hard. A reader of the naive model sees one
  object with all the fields. A reader of the flyweight model must hold in their
  head which fields live on the shared object, which live in the container, and
  which are passed as parameters. Every method signature grows the extrinsic
  parameters. This is the cost that shows up in code review and never shows up in
  a benchmark.
- **Coupling.** Mildly sacrificed. The container now knows about the factory, the
  flyweight type, and the extrinsic layout. Three things are coupled where one
  was.
- **Consistency.** Favoured, in an unusual way. Because the shared object is
  immutable and canonical, two occurrences that should have the same style
  provably do, since they are the same object. Equality checks collapse to
  pointer identity. Hash consing pushes this the furthest.
- **Mutability.** Sacrificed absolutely, and this is not a matter of degree. The
  intrinsic state must be immutable. There is no partial credit. A single mutable
  field on a shared flyweight is a defect that will show up as a data corruption
  bug across unrelated parts of the program.
- **Operability.** Sacrificed. A memory profiler now shows a small number of
  large-retention objects and a large number of tiny ones, and the relationship
  between them is not visible in a heap dump without knowing the design. Pool
  growth becomes a thing that has to be monitored, see dimension 16.
- **Thread safety and contention.** Sacrificed. The pool is shared mutable state
  by construction, which means it needs synchronisation, and that synchronisation
  sits on a hot path. This is the single most commonly botched part of the
  pattern, see dimensions 8 and 11.
- **Lifetime and release.** Sacrificed. A pool that holds strong references
  keeps every flyweight alive for as long as the pool lives. Microsoft documents
  exactly this for the .NET intern pool, warning that memory allocated for
  interned strings is not likely to be released until the common language runtime
  terminates
  ([Microsoft .NET API documentation, String.Intern, Performance considerations](https://learn.microsoft.com/en-us/dotnet/api/system.string.intern),
  verified 2026-08-02).
- **Cost of change.** Sacrificed. Adding a field to the model now requires a
  decision about which side of the intrinsic and extrinsic line it falls on, and
  getting it wrong either explodes the number of pool entries or corrupts shared
  state.

The pattern trades almost everything for one thing. That is a fair trade only
when that one thing is the binding constraint.

## 4. Applicability and non-applicability

Reach for Flyweight when all of the following hold, not merely some.

- The application creates a very large number of objects and memory or garbage
  collection pressure is a measured problem, not a suspected one.
- Removing intrinsic state from the objects would shrink them substantially,
  which means the intrinsic portion is most of the object.
- The intrinsic state's distinct-value count is small relative to the object
  count, so sharing collapses many into few.
- The intrinsic state is immutable, or can be frozen.
- The object identity of individual instances does not matter to the program. If
  code anywhere relies on two logically distinct occurrences being distinguishable
  by reference identity, sharing silently breaks it.
- The extrinsic state has a natural home, usually in the container that iterates
  over the flyweights.

Do NOT reach for Flyweight in these cases. This non-applicability list is the
more useful of the two, and the first item on it is the one that matters most.

- **You have not measured.** Flyweight is a memory optimisation and it is almost
  always premature. The reasoning is direct. The pattern's only benefit is
  memory, its costs are paid in code clarity, lookup time, thread-safety risk and
  lifetime complexity, and those costs are paid on day one whether the benefit
  arrives or not. Unlike most patterns, applying it speculatively does not leave
  the design better arranged for the future. It leaves the design worse and
  slower with no compensating gain. The correct default is a plain object model,
  a heap profile taken under a realistic workload, and Flyweight introduced only
  once the profile names the object type and the retained size. Dimension 14
  gives the refactoring path, which is deliberately mechanical because the point
  is to apply it late and cheaply rather than early and speculatively.
- **The object count is small.** Below a few thousand objects, the pool, the
  factory, the key type and the synchronisation cost more bytes of code than they
  save bytes of heap, and cost more reader attention than either.
- **The intrinsic state has too many distinct values.** If nearly every object's
  shared fields are distinct, the pool grows to one entry per object plus map
  overhead, which uses strictly more memory than not sharing at all. Measure the
  distinct count before writing the factory.
- **The state is mutable and must stay mutable.** A shared object with a mutable
  field is not a flyweight, it is a race condition with a design pattern name.
  If the state has to change per occurrence, it is extrinsic by definition, so
  either move it out or do not share.
- **Reference identity carries meaning in your model.** If the program uses
  identity comparison to tell two occurrences apart, or uses per-instance locks,
  or attaches per-instance metadata through an identity map, sharing merges
  things the program believes are separate. The symptom is subtle and appears far
  from the change.
- **The objects are exclusively owned and returned.** That is Object Pool, a
  different pattern with an opposite lifecycle. Flyweights are shared
  concurrently and never returned. Pooled objects are checked out, mutated,
  checked back in, and reset. Conflating the two produces a pool that hands the
  same mutable object to two callers.
- **The heavy field is already shared by the runtime.** Immutable strings in
  Java, .NET and Python are reference types already. Two objects holding the same
  string field share one string body regardless of what you do. Interning that
  string saves the duplicate string bodies only when the strings are constructed
  at runtime from distinct char arrays, for example parsed from input. For
  literals it saves nothing in Java, where the specification mandates that a
  literal always refers to the same instance, and it is the one case where .NET
  differs, because the C# compiler emits the `NoStringInterning` relaxation by
  default so .NET literals are not guaranteed to be pooled, see dimension 9.
  Applying Flyweight to something the platform already shares is pure cost.
- **The extrinsic state would have to be threaded through twenty call frames.**
  If passing the context down turns every signature in a subsystem into a
  parameter-list mess, the readability cost has exceeded the memory benefit. Look
  at storing extrinsic state in a parallel array in the container instead, or at
  abandoning the pattern.
- **You are chasing allocation rate, not live-set size.** A generational
  collector collects short-lived objects almost for free. Flyweight helps with
  objects that are alive at the same time, not with objects that are created and
  dropped in a loop. If the profile shows high allocation rate but a flat live
  set, the fix is escape analysis, value types, or reuse, not a shared pool.

## 5. Structure

Five participants, named by the role each plays. Note that the GoF structure
carries an unshared concrete flyweight, which most modern descriptions drop and
which matters more than it looks.

- **Flyweight.** The interface through which flyweights receive extrinsic state
  and act on it. Every operation that depends on context takes that context as a
  parameter rather than reading it from a field. This parameterisation is the
  visible signature of the pattern.
- **ConcreteFlyweight.** The shareable implementation. It stores intrinsic state
  only, and it must be immutable and independent of any particular context. One
  instance stands in for every occurrence with the same intrinsic values. In the
  document editor example this is the styled character, holding the codepoint,
  family, size and weight, and knowing nothing about the page.
- **UnsharedConcreteFlyweight.** An implementation of the same interface that is
  not shared. The pattern permits sharing without requiring it, which is what
  lets a Composite tree be built out of flyweights: leaf nodes are shared, the
  interior nodes that hold child lists are not, and the client treats both
  uniformly. Dropping this participant is the reason many descriptions of the
  pattern cannot explain how Flyweight and Composite work together.
- **FlyweightFactory.** Creates and manages the flyweight pool, and guarantees
  that flyweights are shared properly. On a request for a flyweight with given
  intrinsic values it returns the existing instance if one exists and otherwise
  creates, stores and returns a new one. This participant is the only place in
  the design allowed to construct a ConcreteFlyweight. That restriction is what
  makes canonicalisation total, and it is why the constructor should be private
  or the type unexported.
- **Client.** Holds or computes the extrinsic state, obtains flyweights from the
  factory rather than by construction, and passes the extrinsic state into
  operations. The client is usually a container: a document, a tile map, a
  scene graph, a column of a table.

Relationships. Client depends on FlyweightFactory and on the Flyweight
interface, never on ConcreteFlyweight. FlyweightFactory holds an aggregation of
Flyweight instances that outlives any single client operation. ConcreteFlyweight
holds no reference back to any client and no reference to extrinsic state, which
is what allows the same instance to be reachable from many clients at once
without any of them interfering with the others.

The key structural constraint is negative rather than positive. It is not that
the flyweight has certain fields, it is that it must not have certain fields.
Any field whose value would differ between two occurrences that share the
flyweight is a defect.

## 6. ASCII structure diagram

```
   +------------------+  asks for      +-------------------------+
   |     Client       |  flyweight     |    FlyweightFactory     |
   |------------------|  ------------> |-------------------------|
   | extrinsic state  |                | - pool: Map<Key, FW>    |
   | (x, y, index)    |  <-----------  | + get(key): Flyweight   |
   +------------------+  shared ref    +-------------------------+
            |                                      |
            | calls op(extrinsic)                  | owns, keeps alive
            v                                      v
   +--------------------------------------------------------------+
   |                        Flyweight                             |
   |--------------------------------------------------------------|
   | + operation(extrinsicState)                                  |
   +--------------------------------------------------------------+
              ^                                    ^
              | implements                         | implements
              |                                    |
   +-------------------------+        +----------------------------+
   |   ConcreteFlyweight     |        | UnsharedConcreteFlyweight  |
   |-------------------------|        |----------------------------|
   | - intrinsicState        |        | - allState                 |
   |   (immutable, shared)   |        |   (not shared, may hold    |
   | + operation(extrinsic)  |        |    children of either kind)|
   +-------------------------+        +----------------------------+

   Two hard invariants.
   1. ConcreteFlyweight has no field that varies per occurrence.
   2. No path constructs a ConcreteFlyweight except the factory.
```

## 7. Dynamics

The runtime flow has one property that separates a real flyweight from a cache.
The second request for the same key does not merely avoid work, it returns the
identical object that the first request returned, and that identity is a
guarantee the client is allowed to depend on.

```
Client            FlyweightFactory        pool           ConcreteFlyweight
  |                      |                  |                     |
  |-- get("Inter",12) -->|                  |                     |
  |                      |-- probe(key) --->|                     |
  |                      |<-- miss ---------|                     |
  |                      |-- new ---------------------------->    |
  |                      |-- store(key, fw) >|                    |
  |<-- fw ---------------|                  |                     |
  |                      |                  |                     |
  |-- get("Inter",12) -->|                  |                     |
  |                      |-- probe(key) --->|                     |
  |                      |<-- hit (same fw) |                     |
  |<-- fw (identical) ---|                  |                     |
  |                      |                  |                     |
  |  loop over 400k occurrences, extrinsic x held by the client   |
  |                      |                  |                     |
  |-- fw.draw(x=12, y=40) ------------------------------------->  |
  |<-- ink at (12,40) using intrinsic font --------------------   |
  |-- fw.draw(x=19, y=40) ------------------------------------->  |
  |<-- ink at (19,40) using the SAME instance -----------------   |
  |                      |                  |                     |
```

Three timing notes that matter in production.

First, the miss path is the one that races. Between the probe returning a miss
and the store completing, another thread can run the same sequence for the same
key. Without synchronisation the pool ends up with one of the two instances and
the other escapes to a client, which breaks the identity guarantee for that key
forever. Dimension 11 covers the observable symptom.

Second, the pool is monotonic in the simple form. Nothing removes entries, so
the pool's memory is a permanent baseline for the process. This is a design
decision, not an oversight, and it is only correct when the key space is
genuinely bounded. Dimension 8 covers the bounded and weak variants.

Third, the extrinsic state never touches the factory. If the code passes
positional or per-occurrence data into the factory's key, the pool's entry count
becomes the occurrence count and the pattern has inverted into a memory leak.

## 8. Implementation variants

**Map-backed factory, the textbook form.** A hash map from an intrinsic key to
the shared instance, with a single accessor that probes then creates. Simplest,
and the right starting point. The key must implement value equality and hashing
correctly, and in languages with structural equality on records this is free.
The failure mode is unbounded growth.

**Value-as-key, no separate key type.** When the flyweight is itself immutable
and hashable by value, the map becomes a set and the key is the object. This is
what interning is. It removes the key type and removes the possibility of the key
and the object drifting apart, at the cost of constructing a throwaway instance
on every lookup to serve as the probe. In a language with cheap stack allocation
this is fine. In a language where the probe allocates on the heap, it turns every
cache hit into an allocation, which defeats part of the purpose.

**Weak-valued pool.** The pool holds weak references so that a flyweight nobody
else references becomes collectable. This bounds memory in exchange for losing
the guarantee that a given key always maps to the same instance across time,
because the instance can die and be recreated. Identity within a single live
reference chain is still guaranteed, which is what most code actually needs.
Guava provides both shapes explicitly, documenting `newWeakInterner` as returning
a thread-safe interner that retains a weak reference to each instance and so does
not prevent collection, and `newStrongInterner` as retaining a strong reference
and preventing collection
([Guava API documentation, com.google.common.collect.Interners](https://guava.dev/releases/snapshot-jre/api/docs/com/google/common/collect/Interners.html),
verified 2026-08-02). Choosing between them is choosing between bounded memory
and stable identity.

**Bounded pool with eviction.** A most-recently-used or least-recently-used cache
in place of the map. This is the only variant that safely handles an unbounded
key space. FreeType's cache sub-system takes this shape for glyph data,
documented as limiting the number of concurrently open `FT_Face` and `FT_Size`
objects and caching character maps and glyph images while limiting maximum memory
use, with an `FTC_Manager` corresponding to one instance of the sub-system
([FreeType 2 API reference, Cache Sub-System](https://freetype.org/freetype2/docs/reference/ft2-cache_subsystem.html),
verified 2026-08-02). Note what evicting costs. The identity guarantee weakens
to identity-while-cached, so any code comparing flyweights by reference must be
audited before eviction is added.

**Preallocated finite pool.** When the intrinsic key space is small and known at
build time, allocate every flyweight eagerly at startup and make the lookup an
array index rather than a hash probe. This removes the miss path entirely, which
removes the race, the synchronisation, and the growth. Java's mandated
`Integer.valueOf` cache is this variant, see dimension 9. It is the strongest
form and should be preferred whenever the key space allows it.

**Extrinsic state passed as parameters.** The GoF form. Every operation takes the
context. Keeps the flyweight completely free of context, at the cost of long
signatures and the discipline to keep them long.

**Extrinsic state held in a parallel container.** The client stores a
struct-of-arrays layout: one array of flyweight references, one array of
positions. This is the form used in games and columnar databases, because it is
also the layout the CPU wants. It changes the pattern from an object-oriented
shape into a data-oriented one while keeping the same intrinsic and extrinsic
split.

**Instancing, the GPU variant.** The shared mesh and textures are uploaded once
and a buffer of per-instance transforms is uploaded alongside, so the hardware
draws many copies from one geometry stream. Robert Nystrom describes this
directly in *Game Programming Patterns*, explaining that instanced rendering
takes two streams of data, the blob of common data to be rendered many times
being the mesh and textures, and the list of instances and their parameters used
to vary that common data each time it is drawn
([gameprogrammingpatterns.com, Flyweight](https://gameprogrammingpatterns.com/flyweight.html),
verified 2026-08-02). That is the intrinsic and extrinsic split expressed as two
GPU buffers.

**Language note on Rust.** Rust expresses the pattern with `Rc<T>` or `Arc<T>`
plus a map, and the borrow checker makes the immutability requirement mechanical
rather than a convention, because a shared `Rc<T>` gives out only immutable
references unless interior mutability is opted into explicitly. Rust also has a
compile-time flavour, where a string literal is a `&'static str` pointing into
the binary's read-only data and identical literals are commonly merged into one
allocation by the compiler and linker. That merging is an optimisation rather
than a language guarantee, unlike the Java literal rule in dimension 9, so it is
not something a program may depend on for identity.

**Language note on Go.** Go has no inheritance, so the Flyweight participant is a
plain interface and the unshared variant is another implementing type. Because Go
maps are not safe for concurrent use with writes, the factory must carry a mutex
or use `sync.Map`. A plain map behind no synchronisation in a Go flyweight
factory is a data race that the race detector will find and that production will
find first. The `sync.Map` method `LoadOrStore` fits well here because it returns
the value that won the race and discards the loser, which is exactly the
semantics the pattern needs on the miss path.

**Language note on Python.** The dictionary read is atomic under the global
interpreter lock in CPython builds that have one, but the check-then-insert
sequence still needs a lock or an atomic `setdefault` under free-threaded builds
and to preserve the identity guarantee. Python also ships the pattern in the
standard library through `sys.intern`, see dimension 9.

## 9. Known production uses

**Java string literal interning, mandated by the language specification.** The
Java Language Specification states that a string literal always refers to the
same instance of class `String`, because string literals, and more generally
strings that are the values of constant expressions, are interned so as to share
unique instances, as if by execution of the method `String.intern`. Java SE 21
Language Specification, section 3.10.5, String Literals
(https://docs.oracle.com/javase/specs/jls/se21/html/jls-3.html, verified
2026-08-02). This is Flyweight promoted to a language guarantee. The intrinsic
state is the character sequence, there is no extrinsic state because a string
occurrence carries none, and the factory is the runtime's own string pool. It is
the most-executed instance of the pattern in the world and most Java developers
have never thought of it as a pattern at all.

**Java boxed integer caching, with a mandated pool range.** The `Integer.valueOf`
documentation states that the method will always cache values in the range -128
to 127, inclusive, and may cache other values outside of this range, and
recommends it over the constructor because it is likely to yield significantly
better space and time performance by caching frequently requested values. Java SE 21 API
documentation, `java.lang.Integer.valueOf(int)`
(https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/Integer.html,
verified 2026-08-02). This is the preallocated finite pool variant from dimension
8, with the pool range written into the specification so that autoboxing of small
integers is guaranteed to share. It is also the source of one of the most famous
surprises in Java, that reference comparison of two boxed integers succeeds for
small values and fails for large ones, which is the identity guarantee leaking
into code that should never have depended on it.

**.NET string interning through a runtime-managed pool.** Microsoft documents
that the common language runtime maintains a table called the intern pool that
holds a single reference for each unique string value, and that `String.Intern`
uses the pool to search for a string equal to the given value, adding one if
absent. The same page documents that automatic interning of literals is not
guaranteed, depending on how the assembly was compiled, and that the C# compiler
by default emits `CompilationRelaxations.NoStringInterning`
([Microsoft .NET API documentation, String.Intern](https://learn.microsoft.com/en-us/dotnet/api/system.string.intern),
verified 2026-08-02). This is worth contrasting against the Java case above,
because it is the same pattern with the guarantee deliberately weakened for
performance, and it demonstrates that the identity guarantee is a design choice
rather than an inevitability.

**Python string interning in the standard library.** `sys.intern` enters a string
in the table of interned strings and returns the interned string, and the
documentation states that interning is useful to gain a little performance on
dictionary lookup, because if the keys in a dictionary are interned and the
lookup key is interned, the key comparisons after hashing can be done by a
pointer compare instead of a string compare. It also records that names used in
Python programs are automatically interned, and that dictionaries holding module,
class or instance attributes have interned keys. Python 3 documentation, `sys`
module, `sys.intern`
(https://docs.python.org/3/library/sys.html, verified 2026-08-02). The same entry
carries the lifetime warning that interned strings are not immortal and a
reference must be kept to benefit, which is the weak-pool trade from dimension 8
appearing in a standard library. CPython also preallocates a small integer range,
with `_PY_NSMALLPOSINTS` defined as 257 and `_PY_NSMALLNEGINTS` as 5 in
`Include/internal/pycore_global_objects.h`, giving a shared pool from -5 to 256
(https://raw.githubusercontent.com/python/cpython/3.13/Include/internal/pycore_global_objects.h,
verified 2026-08-02). That is an implementation detail of CPython rather than a
language guarantee, unlike the Java case.

**FreeType glyph caching in text rendering.** FreeType, the font rasteriser used
across Linux desktops, Android and many embedded systems, ships a cache
sub-system whose documented purpose is to limit the number of concurrently opened
`FT_Face` and `FT_Size` objects and to cache information such as character maps
and glyph images while limiting their maximum memory usage, managed through an
`FTC_Manager` object that corresponds to one instance of the sub-system
([FreeType 2 API reference, Cache Sub-System](https://freetype.org/freetype2/docs/reference/ft2-cache_subsystem.html),
verified 2026-08-02). The rendered glyph bitmap for a given face, size and
character is intrinsic and shared across every occurrence of that character on
screen. The pen position is extrinsic and lives in the layout code. This is the
Calder and Linton glyph, thirty-five years later, in a shipping C library, with
the eviction variant applied because the key space of face by size by character
is too large to preallocate.

**Unreal Engine instanced static meshes in a game engine.** Epic's documentation
describes an Instanced Static Mesh Component as a component containing a group of
identical static meshes where each mesh within the component represents an
instance of the static mesh asset, and records the memory difference directly,
stating that on the GPU a primitive uses roughly ten times more memory than a
basic instance, 672 bytes against 64 bytes
([Epic Games, Instanced Static Mesh Component in Unreal Engine](https://dev.epicgames.com/documentation/en-us/unreal-engine/instanced-static-mesh-component-in-unreal-engine),
verified 2026-08-02). The mesh and its textures are intrinsic and stored once.
The per-instance transform is extrinsic and stored in a compact per-instance
record. The documentation gives the forest example, that creating a forest by
copying each mesh individually is slow, which is the same forest Nystrom uses in
*Game Programming Patterns*, where he also describes the terrain tile variant,
having each tile that uses the same terrain point to the same terrain instance
([gameprogrammingpatterns.com, Flyweight](https://gameprogrammingpatterns.com/flyweight.html),
verified 2026-08-02).

**Guava interners as a general-purpose library facility.** Google's Guava exposes
the pattern as a first-class library type, with `Interners.newWeakInterner` and
`Interners.newStrongInterner` both documented as returning thread-safe interners,
differing in whether they retain weak or strong references to interned instances
([Guava API documentation, Interners](https://guava.dev/releases/snapshot-jre/api/docs/com/google/common/collect/Interners.html),
verified 2026-08-02). That a widely used library ships the factory as a reusable
component, with the thread-safety promise stated in the contract, is evidence
both that the pattern is common enough to be worth a library and that the
thread-safety concern is real enough to be worth documenting.

## 10. Consequences

Positive.

- Memory use drops in proportion to the ratio of occurrences to distinct
  intrinsic values. Where that ratio is large the reduction is not incremental,
  it is order-of-magnitude, which is why the pattern survives despite its costs.
- A smaller live set reduces garbage collection work on managed runtimes, because
  collection cost scales with live objects traced rather than with garbage.
- Cache locality improves when the per-occurrence record shrinks, which often
  buys throughput on top of the memory saving.
- Equality of intrinsic state collapses to reference comparison, which turns an
  expensive structural comparison into one instruction. Python's documentation
  names this benefit explicitly for interned dictionary keys
  ([Python 3 documentation, sys.intern](https://docs.python.org/3/library/sys.html),
  verified 2026-08-02).
- A fine-grained object model becomes affordable, which is the original Calder
  and Linton motivation and is a design benefit rather than a performance one.
  One object per character is a nicer model than one object per run of characters,
  and Flyweight is what makes it payable.
- The factory is a single chokepoint where instrumentation, validation and
  canonicalisation of intrinsic state can be applied once.

Negative.

- The intrinsic and extrinsic split is a permanent tax on every reader and every
  future change. Every method that needs context must take it as a parameter, and
  the discipline that keeps context out of the flyweight has to be maintained by
  people, because no compiler checks it.
- Runtime cost moves from allocation to lookup. Every flyweight acquisition is a
  hash plus a probe. In a tight loop this can be slower than allocating, and the
  only way to know is to measure both.
- The pool is shared mutable state and needs synchronisation, which introduces a
  contention point on a hot path, see dimension 11.
- A strong pool retains everything forever. The .NET documentation states this
  plainly for its own intern pool
  ([Microsoft .NET API documentation, String.Intern](https://learn.microsoft.com/en-us/dotnet/api/system.string.intern),
  verified 2026-08-02). Applied to an unbounded key space this is a leak with a
  design pattern's name on it.
- Reference identity acquires a meaning it did not have before, and code
  elsewhere starts depending on it, sometimes accidentally. The Java boxed
  integer comparison surprise is the canonical example of that dependency
  becoming a bug.
- Debugging is harder. A breakpoint inside a flyweight method fires for every
  occurrence in the program, not for one, so conditional breakpoints on extrinsic
  state become the only workable technique.
- The pattern resists incremental adoption. Half-applying it, where some
  occurrences share and some do not, produces a model where reference identity
  matters in some places and not in others, which is worse than either extreme.

## 11. Failure modes and misuse

Each entry gives an observable symptom, the cause, and the fix. The symptoms are
drawn from practice rather than from a source.

**Duplicate instances for one key under load.** Symptom. A test asserting that
two lookups of the same key return the identical object passes locally and fails
intermittently in a load test. Or, worse, a pool size gauge that should plateau
at eight terrain types climbs slowly to twelve over hours of traffic, and a heap
dump shows several instances with equal field values. Cause. The factory does a
check-then-act sequence with no synchronisation, so two threads both miss, both
construct, and both store, with the second overwriting the first while the first
instance has already escaped to a caller. This is why an unsynchronised factory
is a real bug and not a theoretical one: it does not fail on the fast path, it
fails on the concurrent miss path, which happens most at startup and under burst
load, precisely when the system is least observable. Fix. Make the miss path
atomic. Use a compute-if-absent operation on a concurrent map, or a lock around
the whole check-then-act, or a lock-free insert that returns the winning instance
and discards the loser. Discarding the loser matters. An implementation that
inserts and returns its own instance regardless of who won reintroduces the bug.
Guava documents its interners as thread-safe for exactly this reason
([Guava API documentation, Interners](https://guava.dev/releases/snapshot-jre/api/docs/com/google/common/collect/Interners.html),
verified 2026-08-02).

**Data race and corrupted map under concurrent writes.** Symptom. In Go, the race
detector reports a concurrent map write and the process dies with a fatal error.
In other languages, a map read returns a torn or impossible value, or an infinite
loop appears inside the map implementation during a resize. Cause. The pool is a
plain hash map written from several goroutines or threads. Fix. A mutex or a
concurrency-safe map type. This failure is more severe than the previous one
because it corrupts the container rather than the sharing guarantee.

**Extrinsic state stored on the flyweight.** Symptom. Characters on page one
render at the position of characters on page four hundred. Or, in a tile map,
every grass tile reports the coordinates of whichever grass tile was touched last.
Or two unrelated HTTP requests see each other's tenant identifier. Cause.
Somebody added a field for context to the shared object, usually as a small
convenience during a refactor, and the shared object now holds whichever value
was written last. Fix. Move the field to the container or to a parameter, and
make the flyweight type immutable at the type level so the mistake cannot be made
again: final or readonly fields, a frozen record, an unexported constructor.

**Pool entry count equal to occurrence count.** Symptom. Memory use after
introducing the pattern is higher than before, and the pool size metric tracks
the object count one to one. Cause. Extrinsic data has been included in the pool
key, so every occurrence produces a unique key. Position, timestamp, request
identifier and object identifier are the usual culprits. Fix. Remove the varying
field from the key. If nothing remains in the key, the pattern does not apply to
this model and should be removed.

**Unbounded pool growth on an open key space.** Symptom. Resident memory climbs
monotonically over days with no matching growth in request volume, and a heap
dump shows retention rooted in one static map. Cause. Interning values that come
from user input, such as request paths, user agent strings, or free-text field
values, where the distinct-value count is effectively unbounded. Fix. Bound the
pool with an eviction policy, switch to weak references, or restrict interning to
a validated allowlist of known values. The .NET documentation warns about exactly
this retention behaviour for its own pool
([Microsoft .NET API documentation, String.Intern](https://learn.microsoft.com/en-us/dotnet/api/system.string.intern),
verified 2026-08-02).

**Lock contention on the factory.** Symptom. Throughput plateaus well below the
CPU count, a profiler shows threads parked, and the stack under the park is the
flyweight factory's lock. The plateau appears after the pattern was introduced to
fix a memory problem, so the team concludes the memory fix caused a slowdown and
half-reverts it. Cause. A single coarse lock around every lookup, including hits.
Fix. Take the lock only on the miss path and read without it where the map
supports concurrent reads, use a concurrency-safe map with striped or lock-free
reads, or preallocate the pool at startup so there is no miss path at all.

**Reference equality assumed where the pool evicts.** Symptom. A comparison that
uses reference identity succeeds under light load and fails under memory
pressure, which makes it look like a memory bug rather than a logic bug. Cause. A
weak or bounded pool was introduced later, so a flyweight was collected and
recreated between two acquisitions of the same key. Fix. Never compare flyweights
by reference unless the pool is strong and non-evicting. Compare by value, or
document the identity guarantee on the factory and forbid eviction.

**Autoboxing identity surprise.** Symptom. A comparison of two boxed integers
with reference equality returns true in tests using small values and false in
production using real identifiers. Cause. The mandated `Integer.valueOf` cache
covers -128 to 127 and may or may not cover anything else
(https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/Integer.html,
verified 2026-08-02), so reference comparison accidentally works inside the pool
range. Fix. Compare boxed values with value equality. This entry is included
because it is the most common way a real production flyweight injures code that
was never aware the pattern was in play.

**Flyweight applied without measurement, then defended.** Symptom. A code review
where the memory saving cannot be quantified, the reviewer asks how much was
saved, and the answer is a hypothesis. The design costs are already paid. Cause.
The pattern was applied because the object count sounded large. Fix. Take the
heap profile. If the retained size of the target type is not among the top
entries, remove the pattern using dimension 14 and keep the profile.

## 12. Trade-off matrix

Compared against named alternatives across the forces from dimension 3. Every
alternative is a real named technique, not a strawman.

| Force | Flyweight | Plain cache or memoization | Object Pool | Interning (runtime built-in) | Singleton | Value object with no sharing | Copy-on-write |
|---|---|---|---|---|---|---|---|
| Primary purpose | Share intrinsic state across many occurrences | Avoid recomputation or refetch | Avoid allocation and teardown cost of expensive resources | Canonicalise one built-in type process-wide | Guarantee exactly one instance | Model correctness by immutability | Defer copying until a write happens |
| Live holders per instance | Many, concurrently | Many, but holders may also compute their own | Exactly one at a time | Many, concurrently | Many, concurrently | One each | Many until first write |
| Is the shared object mutable | Never | Usually the cached value is immutable, not enforced | Yes, and reset between checkouts | Never | Frequently, which is its main defect | Never | Logically yes, physically shared |
| Entries returned or released | Never returned | Evicted by policy | Explicitly returned by the borrower | Never, or weakly collected | Never | Garbage collected normally | Split on write |
| Bounded by construction | No, needs a policy | Yes, eviction is part of the definition | Yes, pool size is configured | Depends, .NET strong, Guava weak available | Yes, one | Yes, no pool exists | Yes, no pool exists |
| Memory effect | Large reduction when distinct values are few | Increase, it trades memory for time | Roughly flat, smooths allocation spikes | Large reduction for that one type | Trivial | None, baseline | Reduction until the first write |
| Latency effect | Lookup added, access improved by locality | Large improvement on hit | Improvement on expensive construction | Lookup added, comparison improved | None | None, baseline | Copy cost moved later |
| Thread-safety burden | High, pool is hot shared state | High, same reason | High, plus checkout accounting | Handled by the runtime or library | High, and worsened by mutability | None | Medium, needs an atomic write barrier |
| Cognitive load | High, the state split is invasive | Low, the API is unchanged | Medium, borrow and return discipline | None, invisible to the caller | Low to write, high to test | Lowest | Medium |
| Correct when state is per-occurrence | No, that is extrinsic | Not applicable | Yes, that is the point | No | No | Yes | Yes |
| Reference identity matters | Yes, and clients depend on it | No | No, identity is incidental | Yes, and this causes surprises | Yes | No | No, and must not |
| Testability | Medium, pool needs isolation between tests | Medium | Medium | Not testable, it is the platform | Poor, global state | Best | Medium |

Reading of the table. Flyweight and a cache are frequently confused because both
are a map in front of a constructor, but they answer different questions. A cache
answers "have I computed this before", is allowed to forget, and does not promise
identity. Flyweight answers "is there already a canonical instance of this
value", is not allowed to forget without weakening its contract, and does promise
identity. Object Pool looks similar again and is the opposite lifecycle: exclusive
ownership, mutation, and return. Interning is Flyweight already implemented for
you on one type, so if the built-in covers the case, using it beats writing a
factory. Singleton shares one instance of a service, which is a different concern
entirely, and shares Flyweight's global-state testing problems without any of its
memory benefit. A plain immutable value object with no sharing is the honest
baseline and is the correct choice until a profile says otherwise. Copy-on-write
is the right pattern when occurrences start identical and a minority later change
independently, which is the case Flyweight cannot handle at all.

## 13. Related and incompatible patterns

- **Factory Method and Abstract Factory.** The FlyweightFactory is normally
  implemented as a factory method or a static factory method, and the enforcement
  that only the factory may construct a ConcreteFlyweight is what makes the
  sharing total. Flyweight depends on a factory being the sole construction path
  in a way that most patterns do not. If any code path can call the constructor
  directly, the canonicalisation guarantee is void.
- **Composite.** Composes above it, and this is the pairing the GoF structure
  supports through the UnsharedConcreteFlyweight participant. In a Composite tree
  of flyweights, leaves are shared and interior nodes holding child lists are not,
  because a child list is per-occurrence state. This is precisely how a document
  editor built out of glyphs works: shared character glyphs, unshared row and
  column glyphs.
- **Singleton.** Adjacent and often confused. A Singleton restricts a type to one
  instance for the whole process. Flyweight allows many instances, one per
  distinct intrinsic value, and the count is a property of the data rather than
  of the type. A flyweight pool that happens to contain a single entry is not a
  Singleton, and a Singleton holding mutable state violates everything Flyweight
  requires.
- **Prototype.** An alternative when occurrences start alike and then change
  independently. Prototype clones a template so each holder gets a private copy
  that can change. Flyweight shares so no holder can change anything. The
  decision between them is the decision about whether occurrences later differ,
  and Copy-on-write is the hybrid.
- **Proxy.** Composes cleanly and appears together in practice. A proxy holding a
  lightweight handle in place of a heavy resource, and resolving it to a shared
  flyweight on demand, is the shape of most texture and font handle systems.
- **Object Pool.** Actively conflicts if mixed. Object Pool exists to recycle
  mutable objects between exclusive owners. Flyweight exists to share immutable
  objects between simultaneous owners. Implementing one and calling it the other
  produces a system that hands a mutable object to two callers who then corrupt
  each other's state. Keep the two vocabularies apart in a codebase.
- **Memoization.** Related in mechanism, different in contract. Memoization caches
  a function result and may forget it. Flyweight canonicalises a value and clients
  may rely on identity. A memoized constructor becomes a flyweight factory only
  once the identity guarantee is promised and eviction is removed.
- **Value Object.** The prerequisite. Flyweight is only sound on types that are
  already value objects, meaning immutable with value-based equality and hashing.
  If the type is not a value object, making it one is the first refactoring step,
  see dimension 14.
- **Data-oriented design and structure-of-arrays layouts.** Effectively supersede
  Flyweight in the hottest paths. Where Flyweight keeps an object per occurrence
  and shrinks it, a structure-of-arrays layout removes the per-occurrence object
  entirely and stores an index into a shared table. The intrinsic and extrinsic
  split survives, the objects do not.
- **Mutable shared state.** The one genuine incompatibility, recorded in the
  frontmatter. Any design that requires a shared object to be written to cannot
  use this pattern. There is no variant that resolves this, because the immutable
  intrinsic state is the pattern's whole premise rather than an implementation
  choice.

## 14. Refactoring path in and out

Introducing the pattern into code that does not have it. This path is written to
be reversible at every step, because the pattern should be applied late, after
measurement, and abandoned quickly if the profile does not support it.

1. Take a heap profile under a realistic workload. Record the retained size and
   instance count of the target type. Write those two numbers down. Without them
   there is no way to know later whether the change paid, and no way to defend it
   in review. If the target type is not near the top of retained size, stop here.
2. Count the distinct values of the candidate intrinsic fields on the same
   workload, by hashing the tuple of those fields across live instances and
   counting unique results. The expected saving is roughly the instance count
   divided by that distinct count. If the ratio is near one, stop here. This step
   catches the pool-entry-count failure from dimension 11 before any code is
   written.
3. Split the fields on paper into intrinsic and extrinsic. For each field, ask
   whether two occurrences that share the object could ever want different values.
   Any yes makes the field extrinsic. Resist the temptation to call a field
   intrinsic because it is usually the same.
4. Extract the intrinsic fields into a new immutable type with value equality and
   hashing. Change the original class to hold an instance of it. Nothing is shared
   yet and nothing has been saved yet. Run the tests. This is Extract Class
   followed by Change Value to Reference, see the refactoring family entries for
   both.
5. Make every construction of the original class go through a single function.
   Still no sharing. Run the tests. This step is the one that makes the next step
   a one-line change and makes it revertible with a one-line change.
6. Add the pool inside that function, with the miss path made atomic from the
   first commit rather than added later. Run the tests, then run a concurrency
   test that hammers the factory from many threads and asserts that the pool size
   equals the distinct key count.
7. Move the extrinsic fields off the shared type, changing the operations that
   used them into operations that take them as parameters. This is the invasive
   step and the one that changes signatures across the subsystem. Do it after the
   pool exists, so that the memory benefit is already measurable and the effort is
   justified rather than speculative.
8. Freeze the shared type. Make the fields final or readonly, make the constructor
   private or unexported, and add a test that asserts no public constructor
   exists. Without this the extrinsic-state-on-the-flyweight failure from
   dimension 11 will eventually happen.
9. Re-profile against the numbers from step one and record the delta in the commit
   message. If the delta is small, take the pattern out using the path below.
10. Add the pool-size gauge from dimension 16 before the change reaches
    production, not after the first incident.

Removing the pattern when it stops earning its place. Signals include a pool size
that tracks the occurrence count, a memory profile where the type no longer
appears, a key space that has become user-driven, or a subsystem where the
extrinsic parameter threading has become the dominant source of review comments.

1. Confirm from the profile that the saving is now small. Removal is a
   performance-affecting change and deserves the same evidence as introduction.
2. Audit every reference-identity comparison on the flyweight type. These are the
   only places where removal changes behaviour rather than only performance, and
   they must be converted to value equality first, in their own commit.
3. Change the factory to construct a new instance on every call, keeping the same
   signature. The pool is now dead but the shape is unchanged. Run the tests and
   the concurrency test. Behaviour should be identical if step two was complete.
4. Delete the pool and its synchronisation.
5. Move the extrinsic parameters back onto the type where that simplifies the
   signatures, one operation at a time.
6. Inline the intrinsic type back into the original class if nothing else uses it.
   This is Inline Class, see the refactoring family entry.
7. Remove the pool-size instrumentation and its alerts, so the dashboard does not
   carry a dead panel.

## 15. Testing and verification

This dimension is practice rather than sourced fact.

Easier because of the pattern.

- Equality assertions become cheap and exact. Asserting that two occurrences share
  a style is a reference comparison rather than a field-by-field comparison.
- The factory is a single seam where every construction can be counted, so an
  allocation-counting test is a wrapper around one function rather than a
  profiler run.
- The immutability requirement makes the flyweight type trivially testable in
  isolation, because it has no lifecycle, no dependencies and no order-sensitive
  behaviour.

Harder because of the pattern.

- Test isolation breaks when the pool is static or process-wide. One test's
  interning affects the next test's pool size assertion, and test order starts to
  matter. This is the same global-state problem Singleton has.
- The memory benefit, which is the only reason the pattern is present, is not
  assertable by a normal unit test. It needs a dedicated measurement step.
- Concurrency correctness on the miss path cannot be established by a
  single-threaded test, and the bug is timing-dependent, so an ordinary test suite
  will report green on a broken factory.

Techniques that apply.

- **Identity test per key.** Two acquisitions of the same key must return the
  identical instance, and two acquisitions of different keys must not. Four lines,
  and it pins the central contract.
- **Immutability test on the flyweight type.** Assert reflectively that every
  field is final or readonly, and that no public constructor exists. This catches
  the field somebody adds during a future refactor, which is the failure that
  causes cross-context corruption.
- **Distinct-count test on a realistic corpus.** Feed the factory a representative
  input set and assert that the pool size equals the expected number of distinct
  keys. This is the test that catches extrinsic state leaking into the key, and it
  is the single highest-value test in this list because that failure inverts the
  pattern into a leak.
- **Concurrency stress test on the miss path.** Start many threads that all
  request the same not-yet-created key at once, using a barrier so they arrive
  together, then assert that every returned reference is identical and that the
  pool holds one entry. Repeat with many keys. Run it under a race detector where
  the language has one, which for Go means the race detector and for Java or C#
  means a thread-sanitiser build or a targeted stress run. Without this test, the
  duplicate-instance failure from dimension 11 ships.
- **Fresh factory per test.** Prefer an injected factory instance to a static
  pool, so each test gets a clean pool. Where the pool must be static, provide a
  test-only reset and call it in setup, and accept that the tests cannot run in
  parallel.
- **Memory assertion at the integration level.** Construct the realistic
  workload, take a heap measurement, and assert an upper bound on retained size
  for the type. Keep the bound loose enough to survive runtime differences and
  tight enough to catch a regression that reintroduces per-occurrence
  construction. This is the only test that verifies the pattern is doing its job.
- **Property test on the intrinsic and extrinsic split.** Generate random
  extrinsic contexts, call the operation with the same flyweight, and assert that
  the flyweight's observable state is unchanged after every call. A failure means
  a context-dependent field has crept onto the shared object.

## 16. Observability signals

This dimension is practice rather than sourced fact. The pattern's whole benefit
lives in memory, and memory is the thing least visible in ordinary application
telemetry, so a flyweight that is not instrumented is a flyweight nobody can tell
is broken.

What to record.

- **Pool size gauge, per pool.** The number of distinct flyweights held. This is
  the single most informative reading. Its expected shape is a fast rise during
  warm-up followed by a plateau.
- **Pool hit and miss counters.** Hit ratio after warm-up should be very close to
  one. A persistent miss rate means the key space is larger than the design
  assumed.
- **Estimated retained bytes for the pool.** Pool size multiplied by an average
  entry size, or a real measurement if the runtime allows it. This lets an
  operator see the pool's memory as a first-class number rather than inferring it
  from a heap dump.
- **Occurrence-to-flyweight ratio.** Live occurrence count divided by pool size.
  This is the pattern's return on investment expressed as one number, and it is
  the number to put on the dashboard next to the pool size.
- **Factory lock wait time, as a histogram.** Only where a lock is used. This is
  what catches the contention failure before it becomes a throughput incident.
- **Eviction counter and eviction reason**, for bounded pools. A rising eviction
  rate on a pool that was sized for the workload means the workload changed.
- **Construction counter for the flyweight type**, distinct from the miss counter.
  If constructions exceed misses, something is bypassing the factory, which means
  the canonicalisation guarantee is already void.

A healthy instance on a dashboard. Pool size rises during the first minutes after
a deploy and then goes flat, and stays flat across days. Hit ratio sits above
0.999 after warm-up. The occurrence-to-flyweight ratio is large and stable, in
the hundreds or thousands for a case where the pattern is earning its keep. Lock
wait time stays at the measurement resolution limit. Constructions equal misses
exactly. Resident memory is flat over a week under steady traffic.

A failing instance. Pool size climbs linearly with request volume and never
plateaus, which is the unbounded-growth failure and the one that ends in an
out-of-memory kill, and the occurrence-to-flyweight ratio sitting near one
confirms it. Or pool size exceeds the known distinct-key count by a small margin
that grows slowly, which is the duplicate-instance race, and it is worth alerting
on because nothing else reveals it. Or hit ratio degrades after a deploy, which
usually means a new field entered the key. Or lock wait time develops a long tail
that correlates with request concurrency rather than with request volume, which
localises the contention failure. Or constructions exceed misses, which means a
direct constructor call was added and the pool is no longer canonical.

## 17. Security and privacy implications

This dimension is analytical. The pattern is close to silent on security in its
closed form, where the key space is bounded and internal, and claiming otherwise
would be inventing a concern. Four genuine implications appear once the key space
is reachable by an untrusted party or once the shared objects outlive a request.

**Memory-exhaustion denial of service through an open key space.** This is the
real one. A pool keyed by anything an attacker controls, such as a header name, a
URL path segment, a tenant label, a metric tag or a free-text field, gives the
attacker a direct write into a structure that never shrinks. Each distinct value
adds a permanent entry. The attack requires no privilege, produces no error, and
looks like ordinary traffic until the process dies. It is the same shape as the
label explosion that breaks metrics systems. Defences are to key the pool only
from a validated allowlist of known values, to bound the pool with eviction and
treat eviction rate as an alarm, and to alert on pool size growth rather than
only on process memory, since pool size crosses its abnormal threshold long
before resident memory does.

**Cross-context data disclosure through mistaken extrinsic state.** Because the
flyweight is reachable from every context at once, a field wrongly placed on the
shared object is visible to every context at once. When that field holds a tenant
identifier, a user identifier, an authorisation decision or a locale-derived
personal attribute, the bug is not a rendering glitch, it is a data disclosure
across tenants. The failure is described in dimension 11 as a correctness bug and
is repeated here because its security severity is much higher than its
correctness severity suggests. The defence is structural immutability enforced by
the type system plus the reflective immutability test from dimension 15, rather
than a code review convention.

**Timing side channel on the pool.** A pool lookup is measurably faster on a hit
than on a miss, and an attacker who can time requests and influence the key can
learn whether a given value has been seen before by the process. Where the keyed
value is a secret or a user-existence indicator, this leaks membership. This is
the same class of leak as a cache-timing oracle and the same defences apply. Do
not intern secrets, and where a value must be canonicalised and is sensitive,
preallocate the full key space so hit and miss timings are identical.

**Retention beyond the intended lifetime.** A strong pool keeps its contents for
the life of the process, which means anything interned survives logout, session
end, tenant offboarding and, in the .NET case, application domain teardown, since
Microsoft documents that the runtime's reference can persist after the
application or the application domain terminates
([Microsoft .NET API documentation, String.Intern, Performance considerations](https://learn.microsoft.com/en-us/dotnet/api/system.string.intern),
verified 2026-08-02). Under a data-deletion obligation, a right-to-erasure
request that deletes rows from a database does not touch a process-wide intern
pool holding the same values, and no ordinary deletion audit will find them.
Personal data should not be interned. Where a value must be canonicalised and
also deleted on request, use a weak or evicting pool scoped to a request or a
session rather than to the process.

On privacy the pattern is otherwise neutral. The observability advice in dimension
16 records counts and sizes rather than values, which is deliberate. A pool
inspection endpoint that dumps keys would expose whatever was interned, so if such
an endpoint exists it inherits the classification of the most sensitive value in
the pool and should be treated accordingly.

## 18. References

1. Erich Gamma, Richard Helm, Ralph Johnson, John Vlissides. *Design Patterns.
   Elements of Reusable Object-Oriented Software*. Addison-Wesley, 1994.
   ISBN 0-201-63361-2. Chapter 4, Structural Patterns, section Flyweight. Source
   of the five participants including UnsharedConcreteFlyweight, the intrinsic
   and extrinsic split as the organising idea, and the pairing with Composite.
   The page range was not independently confirmed and is therefore not cited.
2. Paul R. Calder, Mark A. Linton. "Glyphs: flyweight objects for user
   interfaces". Proceedings of the 3rd annual ACM SIGGRAPH symposium on User
   Interface Software and Technology, UIST 1990, Snowbird, Utah, pages 92 to 101.
   DOI 10.1145/97924.97935. Bibliographic record verified at
   https://dblp.uni-trier.de/rec/conf/uist/CalderL90.html
   Verified 2026-08-02. Source of the pattern's origin and the WYSIWYG document
   editor motivation. The full text was not read, so no claim in this entry
   quotes its contents beyond the title and the bibliographic facts.
3. Oracle. *The Java Language Specification, Java SE 21 Edition*, section 3.10.5,
   String Literals.
   https://docs.oracle.com/javase/specs/jls/se21/html/jls-3.html
   Verified 2026-08-02. Source of the mandated string literal interning behaviour.
4. Oracle. *Java SE 21 API Specification*, `java.lang.Integer`, method
   `valueOf(int)`.
   https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/Integer.html
   Verified 2026-08-02. Source of the mandated -128 to 127 cache and the optional
   caching outside that range.
5. Microsoft. *.NET API documentation*, `System.String.Intern(String)`, including
   the Remarks and Performance considerations sections.
   https://learn.microsoft.com/en-us/dotnet/api/system.string.intern
   Verified 2026-08-02. Source of the intern pool description, the statement that
   automatic literal interning is not guaranteed, and the retention warning used
   in dimensions 3, 10, 11 and 17.
6. Python Software Foundation. *Python 3 documentation*, `sys` module,
   `sys.intern`.
   https://docs.python.org/3/library/sys.html
   Verified 2026-08-02. Source of the pointer-comparison benefit for interned
   dictionary keys and the note that interned strings are not immortal.
7. CPython project. `Include/internal/pycore_global_objects.h`, definitions of
   `_PY_NSMALLPOSINTS` and `_PY_NSMALLNEGINTS`.
   https://raw.githubusercontent.com/python/cpython/3.13/Include/internal/pycore_global_objects.h
   Verified 2026-08-02. Source of the CPython small integer pool range of -5 to
   256. This is an implementation detail of CPython, not a language guarantee.
8. FreeType project. *FreeType 2 API Reference*, Cache Sub-System.
   https://freetype.org/freetype2/docs/reference/ft2-cache_subsystem.html
   Verified 2026-08-02. Source of the text rendering production use and the
   bounded-pool variant.
9. Epic Games. *Unreal Engine 5.8 Documentation*, "Instanced Static Mesh Component
   in Unreal Engine".
   https://dev.epicgames.com/documentation/en-us/unreal-engine/instanced-static-mesh-component-in-unreal-engine
   Verified 2026-08-02. Source of the game engine production use and the 672 bytes
   against 64 bytes per-instance memory comparison.
10. Robert Nystrom. *Game Programming Patterns*, chapter on Flyweight.
    https://gameprogrammingpatterns.com/flyweight.html
    Verified 2026-08-02. Source of the forest and terrain tile examples and the
    description of instanced rendering as two data streams.
11. Google. *Guava API documentation*, `com.google.common.collect.Interners`.
    https://guava.dev/releases/snapshot-jre/api/docs/com/google/common/collect/Interners.html
    Verified 2026-08-02. Source of the weak and strong interner variants and the
    documented thread-safety guarantee used in dimensions 8 and 11.
12. Wikipedia contributors. "Flyweight pattern".
    https://en.wikipedia.org/wiki/Flyweight_pattern
    Verified 2026-08-02. Used only to confirm the GoF category, the wording of the
    intrinsic and extrinsic state distinction, and the Calder and Linton
    attribution. Not used as a source of explanation.

## Code examples

Four languages, each showing a part of the pattern the others cannot. Python
shows the classical form with the intrinsic and extrinsic split and a
double-checked factory. TypeScript shows the same shape with a string key and a
frozen product, which is how the pattern appears in most application code. Go
shows the atomic miss path, using `sync.Map.LoadOrStore` so that the instance
which loses the race is discarded rather than handed out. Rust shows reference
counting, where the compiler enforces the immutability of the shared object
rather than leaving it to convention. Java is omitted from the samples because
its most important instances of this pattern are in the platform itself rather
than in user code, and are covered in dimension 9, and because no JDK was
available on the authoring machine to compile a sample.

Every sample below was executed. Python 3.14.6, Go via `go run`, TypeScript type
checked with `tsc --strict` and executed on Node 23.11.0, and Rust compiled with
rustc 1.97.1. All four print a first line of `true 1`, showing that two lookups of
the same key returned the identical object and that the pool holds one entry.

### Python

```python
import threading


class GlyphStyle:
    __slots__ = ("family", "size", "bold")

    def __init__(self, family: str, size: int, bold: bool) -> None:
        object.__setattr__(self, "family", family)
        object.__setattr__(self, "size", size)
        object.__setattr__(self, "bold", bold)

    def __setattr__(self, name: str, value: object) -> None:
        raise AttributeError("flyweight is immutable")

    def advance(self, ch: str) -> int:
        base = self.size // 2 if ch == " " else self.size
        return base + (1 if self.bold else 0)


class StyleFactory:
    def __init__(self) -> None:
        self._pool: dict[tuple[str, int, bool], GlyphStyle] = {}
        self._lock = threading.Lock()

    def get(self, family: str, size: int, bold: bool) -> GlyphStyle:
        key = (family, size, bold)
        hit = self._pool.get(key)
        if hit is not None:
            return hit
        # The miss path must be atomic or two threads produce two instances.
        with self._lock:
            return self._pool.setdefault(key, GlyphStyle(family, size, bold))

    def __len__(self) -> int:
        return len(self._pool)


def layout(text: str, style: GlyphStyle, start_x: int) -> list[tuple[str, int]]:
    x = start_x
    out: list[tuple[str, int]] = []
    for ch in text:
        out.append((ch, x))
        x += style.advance(ch)
    return out


if __name__ == "__main__":
    factory = StyleFactory()
    body = factory.get("Inter", 12, False)
    again = factory.get("Inter", 12, False)
    print(str(body is again).lower(), len(factory))
    print(layout("ab c", body, 0))
```

### TypeScript

```typescript
interface Style {
  readonly family: string;
  readonly size: number;
  readonly bold: boolean;
}

class StyleFactory {
  private readonly pool = new Map<string, Style>();

  get(family: string, size: number, bold: boolean): Style {
    const key = `${family}|${size}|${bold}`;
    const hit = this.pool.get(key);
    if (hit !== undefined) return hit;
    const made: Style = Object.freeze({ family, size, bold });
    this.pool.set(key, made);
    return made;
  }

  get count(): number {
    return this.pool.size;
  }
}

function advance(style: Style, ch: string): number {
  const base = ch === " " ? style.size / 2 : style.size;
  return base + (style.bold ? 1 : 0);
}

function layout(text: string, style: Style, startX: number): [string, number][] {
  let x = startX;
  const out: [string, number][] = [];
  for (const ch of text) {
    out.push([ch, x]);
    x += advance(style, ch);
  }
  return out;
}

const factory = new StyleFactory();
const body = factory.get("Inter", 12, false);
const again = factory.get("Inter", 12, false);
console.log(body === again, factory.count);
console.log(layout("ab c", body, 0));
```

### Go

```go
package main

import (
	"fmt"
	"sync"
)

type Style struct {
	Family string
	Size   int
	Bold   bool
}

func (s *Style) Advance(ch rune) int {
	base := s.Size
	if ch == ' ' {
		base = s.Size / 2
	}
	if s.Bold {
		base++
	}
	return base
}

type StyleFactory struct {
	pool sync.Map
}

// LoadOrStore keeps the winner of a race and drops the loser, which is
// exactly the semantics a shared pool needs on a miss.
func (f *StyleFactory) Get(family string, size int, bold bool) *Style {
	key := Style{Family: family, Size: size, Bold: bold}
	if hit, ok := f.pool.Load(key); ok {
		return hit.(*Style)
	}
	fresh := key
	actual, _ := f.pool.LoadOrStore(key, &fresh)
	return actual.(*Style)
}

func (f *StyleFactory) Count() int {
	n := 0
	f.pool.Range(func(_, _ any) bool {
		n++
		return true
	})
	return n
}

func main() {
	factory := &StyleFactory{}
	body := factory.Get("Inter", 12, false)
	again := factory.Get("Inter", 12, false)
	fmt.Println(body == again, factory.Count())

	x := 0
	for _, ch := range "ab c" {
		fmt.Printf("%c@%d ", ch, x)
		x += body.Advance(ch)
	}
	fmt.Println()
}
```

### Rust

```rust
use std::collections::HashMap;
use std::rc::Rc;

#[derive(PartialEq, Eq, Hash, Clone)]
struct Style {
    family: String,
    size: u32,
    bold: bool,
}

impl Style {
    fn advance(&self, ch: char) -> u32 {
        let base = if ch == ' ' { self.size / 2 } else { self.size };
        base + if self.bold { 1 } else { 0 }
    }
}

#[derive(Default)]
struct StyleFactory {
    pool: HashMap<Style, Rc<Style>>,
}

impl StyleFactory {
    fn get(&mut self, family: &str, size: u32, bold: bool) -> Rc<Style> {
        let key = Style { family: family.to_string(), size, bold };
        if let Some(hit) = self.pool.get(&key) {
            return Rc::clone(hit);
        }
        let shared = Rc::new(key.clone());
        self.pool.insert(key, Rc::clone(&shared));
        shared
    }

    fn count(&self) -> usize {
        self.pool.len()
    }
}

fn main() {
    let mut factory = StyleFactory::default();
    let body = factory.get("Inter", 12, false);
    let again = factory.get("Inter", 12, false);
    println!("{} {}", Rc::ptr_eq(&body, &again), factory.count());

    let mut x = 0;
    for ch in "ab c".chars() {
        print!("{}@{} ", ch, x);
        x += body.advance(ch);
    }
    println!();
}
```
