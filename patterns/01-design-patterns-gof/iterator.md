---
name: Iterator
slug: iterator
family: 01-design-patterns-gof
category: Behavioral
aliases: [Cursor, Enumerator, Enumeration, Sequence Traversal]
first_described: "Gamma, Helm, Johnson, Vlissides 1994"
maturity: canonical
related: [composite, visitor, factory-method, memento, decorator, template-method, null-object]
incompatible_with: []
verified: 2026-08-02
---

# Iterator

## 1. Name, aliases, and lineage

The canonical name is Iterator. It appears in the Gang of Four catalog as a
behavioral pattern, in Erich Gamma, Richard Helm, Ralph Johnson and John
Vlissides, *Design Patterns. Elements of Reusable Object-Oriented Software*,
Addison-Wesley, 1994, chapter 5 (Behavioral Patterns), Iterator, pages 257 to
271. The stated intent is to provide a way of reaching the elements of an
aggregate object one after another without exposing how that aggregate stores
them ([Wikipedia summary of the GoF intent, citing pages 257ff](https://en.wikipedia.org/wiki/Iterator_pattern),
verified 2026-08-02).

The book records **Cursor** as the alias, taken from database practice where a
cursor is a server-side position marker over a result set. Three further names
are in daily use and each carries a slightly different flavour.

- **Enumerator.** The .NET name. `System.Collections.Generic.IEnumerator<T>` is
  the Iterator role and `IEnumerable<T>` is the Aggregate role
  ([Microsoft .NET API documentation](https://learn.microsoft.com/en-us/dotnet/api/system.collections.generic.ienumerator-1),
  verified 2026-08-02).
- **Enumeration.** The pre-1.2 Java name, kept for backward compatibility on
  legacy types, superseded by `java.util.Iterator`.
- **Generator.** A coroutine that produces a sequence. Every generator is an
  iterator, but not every iterator is a generator, because a generator also
  suspends and resumes a call stack. Python makes the relationship explicit. a
  generator function returns a generator object that implements `__next__` and
  returns itself from `__iter__`
  ([Python language reference, yield expressions](https://docs.python.org/3/reference/expressions.html#yield-expressions),
  verified 2026-08-02).

The lineage predates the GoF book by nearly two decades. CLU, designed at MIT by
Barbara Liskov and colleagues, shipped iterators as a first-class control
abstraction, so that a `for` statement could range over a user-defined data
abstraction rather than only over integers. Barbara Liskov, Alan Snyder, Russell
Atkinson and Craig Schaffert, "Abstraction Mechanisms in CLU", *Communications of
the ACM*, volume 20, number 8, 1977, pages 564 to 576
([ACM Digital Library record](https://dl.acm.org/doi/10.1145/359763.359789),
verified 2026-08-02). The GoF contribution was not the idea of a traversal
cursor. It was the observation that the cursor is an object with its own type and
its own lifetime, separable from both the collection and the loop.

One naming distinction is worth fixing early because most catalogs skip it, and
it drives half the design decisions in the rest of this entry. The GoF book asks,
in its Implementation section, who controls the iteration, and gives two answers.

- **External iterator.** The client drives. The client asks for the next element
  and decides when to stop. `java.util.Iterator` with `hasNext` and `next` is the
  archetype.
- **Internal iterator.** The aggregate drives. The client hands over an operation
  and the aggregate applies it to each element. `Iterable.forEach(Consumer)` is
  the archetype, and the Java documentation describes it as performing the given
  action for each element until every element has been processed or the action
  throws ([Java SE 21, `java.lang.Iterable`](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/Iterable.html),
  verified 2026-08-02).

The GoF book is a description of the external form, which is why the classical
diagram shows a cursor object. The internal form is the same pattern with the
control inverted, and it is the form most functional and stream APIs ship.

## 2. Problem and context

A client needs to visit every element of a collection, and the collection knows
how it stores those elements while the client does not and should not.

The situation reads like this in a codebase. There is a container with a real
internal shape, a hash table, a balanced tree, a ring buffer, a linked structure,
a paged remote result set. Some caller wants to run over the contents. The
shortest path is to expose the internals. Publish the backing array, return the
head node, hand out the page token, and let the caller write the loop. That works
once. It fails on the second caller and on the first change of representation.

Four distinct problems appear once the internals are exposed.

- **Every loop encodes the representation.** A change from an array to a tree
  edits every call site. The container's licence to change its own storage is
  gone, which is the whole reason the container exists as an abstraction.
- **Traversal order becomes the caller's problem.** Depth-first, breadth-first,
  in-order, reverse, filtered. The container has one natural order and a caller
  who wants another writes its own walk, which then lives outside the container
  and rots when the container changes.
- **Two simultaneous walks collide.** Index variables held by the caller work
  until two walks over the same structure interleave, or until one walk is
  suspended and resumed later, which is exactly what a paged API or a merge
  requires.
- **Large or endless sequences cannot be handled at all.** Materialising a
  result set into a list to loop over it means the whole set fits in memory. It
  often does not, and for a sequence with no end it never does.

The context in which Iterator is the right answer has three parts.

- The aggregate has a representation the client should not know about, or has
  more than one sensible traversal order, or both.
- The elements are consumed one at a time, in sequence, with no need for random
  access or index arithmetic during the walk.
- The cost of producing the whole sequence at once is unacceptable, or the
  sequence has no end, or the traversal position must survive between calls.

Outside that context the pattern is overhead. A three-element configuration
object does not need a cursor. See dimension 4.

## 3. Forces

The pattern balances the following competing pressures.

- **Coupling.** Favoured strongly. The client depends on the iterator interface
  and on the element type. It depends on nothing about the container's storage.
  This is the largest payoff and the reason the pattern is close to universal.
- **Memory.** Favoured. A lazy iterator holds one element and a position rather
  than the whole sequence. This is what makes streaming and endless sequences
  expressible at all.
- **Latency of the first element.** Favoured. A lazy iterator returns the first
  element after producing one element, not after producing all of them, which
  moves work off the critical path of a request that only needs the head.
- **Throughput on the whole sequence.** Sacrificed. One interface call per
  element, often two in the `hasNext` plus `next` shape, is more work than a
  tight indexed loop over a contiguous array. In a hot numeric loop this is
  measurable, which is why bulk and split forms exist. See dimension 8.
- **Consistency.** Sacrificed, and this is the sharpest edge of the pattern. An
  iterator holds a position into a structure that other code can change. The
  design has to pick between failing loudly, showing a snapshot, or showing a
  live but weakly defined view. There is no free option. See dimension 11.
- **Cognitive load.** Mixed. A `for` loop over an iterable is the easiest
  traversal a reader can meet. A hand-written iterator class holding a stack for
  a tree walk, with the walk turned inside out into a state machine, is among the
  hardest code in a codebase to read. Generators exist to remove that cost.
- **Operability.** Sacrificed. An iterator hides where the elements come from,
  so a page fetch, a database round trip or a disk read can hide behind what
  looks like a local loop. The classic production surprise is an N plus one
  query pattern behind an innocent-looking iteration.
- **Resource lifetime.** Sacrificed. A cursor over a file, a socket or a
  database result set owns a resource whose release is now tied to the loop
  ending, including the case where the loop ends early by an exception or a
  break. Languages answer this with `Dispose`, `close`, `return()` and
  `GeneratorExit`, and each answer is a place a leak can hide.
- **Cost of change.** Favoured for adding a traversal order, since a new order is
  a new iterator and nothing else changes. Sacrificed for changing the element
  type, which ripples through every consumer.
- **Team topology.** Favoured. A platform team can own a container and publish
  the iterator contract, and product teams can write traversals without reading
  the container's source.

A pattern that gave up nothing would not need a catalog entry. Iterator buys
independence from representation and pays in per-element overhead, in a
consistency question that has to be answered explicitly, and in a resource
lifetime that is now implicit in control flow.

## 4. Applicability and non-applicability

Reach for Iterator when the following hold.

- Clients need to reach the contents of an aggregate without learning its
  storage, and the storage is likely to change or already varies between
  implementations of one interface.
- The same aggregate supports several traversal orders and each should be a
  named, testable, separately usable thing.
- The sequence is large enough that materialising it is a memory risk, or is
  produced incrementally from a remote or streaming source.
- The sequence has no natural end, and consumers are expected to take a prefix.
- Traversal must be suspended and resumed, or two traversals must run at once
  over the same aggregate.
- A uniform traversal interface is wanted across container types so that
  algorithms can be written once, which is the design of the C++ Standard
  Template Library and of the Java Collections Framework.
- The traversal produces elements that a pipeline of transformations will
  consume, and each stage should run one element at a time rather than
  materialising an intermediate collection.

Do NOT reach for Iterator in these cases. This non-applicability list is the more
useful half, and the reason for each case matters more than the case.

- **The language gives you iteration already and the container is a standard
  one.** Writing a cursor class over a list in Python, Java, C#, Go, Rust,
  TypeScript or Kotlin is work that the standard library already did. Return the
  standard iterable and stop. A hand-rolled `hasNext` and `next` over an array
  field is code with no reader and one more place for an off-by-one error.
- **The collection is small, fixed, and internal.** A settings object with four
  fields does not need a traversal abstraction. This is speculative generality,
  see the code smell family entry.
- **Callers need random access, sorting, or size.** An iterator gives sequential
  one-pass access. If callers index, sort, count or reverse, they want a list or
  a slice, and forcing that through a cursor produces repeated full traversals
  and quadratic behaviour.
- **The traversal itself is the algorithm you are trying to express.** A tree
  walk that must carry per-node accumulated state, that must dispatch on node
  type, and that must be extended with new operations later, is Visitor
  territory. An iterator flattens the structure into a sequence and throws away
  the shape, which is the very thing the algorithm needed.
- **Consumers must be notified as elements arrive, rather than pulling them.**
  A pull-based cursor cannot express a source that decides when data appears.
  That is Observer, or a reactive streams implementation with backpressure. An
  iterator over a queue that blocks in `next` is a thread parked on a socket,
  which does not scale past a small number of sources.
- **The work per element is large and independent, and parallelism is wanted.**
  A sequential cursor is a serialisation point. Java answers this with a
  splitting traversal object rather than an iterator, see dimension 8.
- **Elements must be removed or inserted during the walk in a structure with no
  support for it.** Mutation during traversal is the single most common
  production failure in this pattern, see dimension 11. If the workload is by
  nature a read-modify-write over a whole collection, build a new collection or
  use a structure that documents concurrent traversal semantics.
- **The cursor would hold a scarce resource across an unbounded caller-controlled
  loop.** Returning a lazy iterator backed by an open database cursor to
  application code hands the connection lifetime to a caller who does not know it
  is holding one. Either materialise inside the resource scope, or make the
  resource ownership explicit in the type and the API contract.
- **The abstraction would leak on the first real use.** If consumers immediately
  cast the iterator back to the concrete container to reach a method the
  interface lacks, the interface is wrong and the pattern is decoration.

## 5. Structure

Five participants, named by the role each plays.

- **Iterator.** The traversal interface. Declares the operations for advancing
  and for reading the current element, and in most forms an operation for asking
  whether anything remains. The minimum useful surface is one operation that
  either yields the next element or reports exhaustion. Optional members are the
  removal operation, a reset, and a release or close.
- **ConcreteIterator.** Holds the traversal state. That state is the actual
  content of the pattern. an index for an array, a node pointer for a list, an
  explicit stack for a depth-first tree walk, a page token and a buffer for a
  remote result set, a saved coroutine frame for a generator. It also usually
  holds a reference to the aggregate, which is what makes concurrent modification
  detectable and also what keeps the aggregate alive.
- **Aggregate.** The container interface. Declares the operation that produces an
  Iterator. That operation is a Factory Method, which is the composition point
  between the two patterns. See dimension 13.
- **ConcreteAggregate.** Implements the container and returns the matching
  ConcreteIterator, usually as a private nested type so that the concrete cursor
  is never a name a client can write.
- **Client.** Holds the Iterator and the element type, and nothing else. The
  client never names the ConcreteIterator and never names the
  ConcreteAggregate's storage.

Relationships. Aggregate has a creation dependency on Iterator. ConcreteAggregate
creates ConcreteIterator and normally grants it privileged access to internals,
through friendship in C++, package or nested-class access in Java, or module
privacy in Rust and Go. That privileged access is deliberate. The cursor is part
of the container's implementation, and the container is the only thing that
should know how the cursor moves.

Two structural variants change the shape enough to be worth naming here rather
than in dimension 8.

- In the **internal** form the Iterator role collapses into a single higher-order
  operation on the Aggregate, and the client supplies a function rather than
  holding a cursor. The ConcreteIterator still exists, but as a loop inside the
  aggregate rather than as a published object.
- In the **push** form used by Go 1.23, the Iterator role is a function value
  that receives a yield callback, which is the internal form given a standard
  signature so that the language loop syntax can consume it. See dimension 8.

## 6. ASCII structure diagram

```
   +------------------------+   creates    +-------------------------+
   |       Aggregate        | - - - - - -> |        Iterator         |
   |------------------------|              |-------------------------|
   | + iterator(): Iterator |              | + hasNext(): bool       |
   +------------------------+              | + next(): Element       |
              ^                            | + remove()   [optional] |
              | implements                 | + close()    [optional] |
              |                            +-------------------------+
   +------------------------+                          ^
   |   ConcreteAggregate    |                          | implements
   |------------------------|                          |
   | - storage              |              +-------------------------+
   | + iterator(): Iterator |   creates    |    ConcreteIterator     |
   +------------------------+ -----------> |-------------------------|
              ^                            | - aggregate ref         |
              | privileged access          | - position / stack /    |
              +--------------------------- |   page token / frame    |
                                           | - expectedModCount      |
                                           +-------------------------+
                                                       ^
   +------------------------+   holds only             |
   |        Client          | -------------------------+
   |------------------------|
   | uses Iterator + Element|
   +------------------------+

   The Client never names ConcreteIterator or the storage field.
   Only the dashed arrow crosses the abstraction boundary.
```

## 7. Dynamics

Two runtime views matter. The first is the call sequence of an external
traversal. The second is the state machine of a single cursor, because most
production bugs in this pattern are a transition that the code did not handle.

```
Client            ConcreteAggregate       ConcreteIterator      Element
  |                       |                       |                |
  |-- iterator() -------->|                       |                |
  |                       |-- new(position=0) --->|                |
  |<-- Iterator ----------|                       |                |
  |                       |                       |                |
  |-- hasNext() ------------------------------->  |                |
  |<-- true ------------------------------------  |                |
  |-- next() ----------------------------------> |                 |
  |                       |<-- read storage ------|                |
  |                       |   advance position    |                |
  |<-- Element ---------------------------------  |                |
  |-- use(Element) ------------------------------------------->    |
  |                       |                       |                |
  |         (loop repeats until hasNext is false) |                |
  |                       |                       |                |
  |-- hasNext() ------------------------------->  |                |
  |<-- false -----------------------------------  |                |
  |-- close()  [only when the cursor owns a resource] --------->   |
  |                       |                       |                |
```

The cursor state machine. Exhausted is absorbing, and the two error edges are
where production incidents come from.

```
                    +---------------+
      iterator()    |    FRESH      |
   ----------------> | position 0    |
                    +---------------+
                        |      |
             next() ok  |      | next() on empty aggregate
                        v      v
                    +---------------+           +--------------+
                    |   ADVANCING   |---------->|  EXHAUSTED   |
                    | 1..n elements |  no more  |  next() is   |
                    +---------------+           |  an error or |
                      |          ^              |  a sentinel  |
      aggregate       |          | next()       +--------------+
      shape changed   |          |                     |
      by other code   v          |                     | next() again
                 +-------------------+                 v
                 |    INVALIDATED    |          same result, forever
                 | next()/hasNext()  |          (protocol requirement)
                 | throw or return   |
                 | undefined data    |
                 +-------------------+
```

Three timing facts follow from this machine and each has cost a real system.

First, the exhausted state has to be sticky. The Python documentation makes this
a contract requirement, stating that once an iterator has raised the stop signal
it must keep raising it, and that implementations which do not obey this are
broken ([Python standard types, iterator types](https://docs.python.org/3/library/stdtypes.html#iterator-types),
verified 2026-08-02). The equivalent .NET rule is that after the advance
operation returns false, later calls also return false and the current element is
undefined, and that the enumerator cannot be rewound to the start without
creating a new one
([Microsoft .NET API documentation, `IEnumerator<T>`](https://learn.microsoft.com/en-us/dotnet/api/system.collections.generic.ienumerator-1),
verified 2026-08-02).

Second, the invalidated transition is not always detected. It is a design choice
made by the container, not a property of the pattern, and dimension 11 covers the
three answers in production use.

Third, in the lazy form no element is produced until the first advance. The C#
documentation demonstrates this directly. calling an iterator method does not run
its body, and the body runs to the first yield only when enumeration starts,
suspending and resuming across each element
([Microsoft C# reference, the yield statement](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/statements/yield),
verified 2026-08-02). Anything with a side effect placed before the first yield
therefore happens later than a reader expects, and never at all if nobody
enumerates.

## 8. Implementation variants

**External iterator, the classical GoF form.** The client holds the cursor and
drives it. Strongest form for control. the client can stop early, interleave two
sequences, hand the cursor to another function, or store it. It is the only form
that composes for a merge or a zip of two sequences, because the merging code
needs to advance each side independently. The cost is that the traversal state
must be written out by hand as fields, which for a recursive structure means
turning a recursive walk into an explicit stack machine.

**Internal iterator.** The aggregate owns the loop and the client passes an
operation. Simplest to write and safest for resource lifetime, because the
aggregate can wrap the whole loop in a resource scope and release on exit for
every exit path. Java's per-element action on the iterable interface is this
form, and the documentation is explicit that exceptions from the action are
relayed to the caller, which is how early exit and error propagation work when
the client has no cursor to break out of. The costs are real. early exit needs a
protocol, usually a boolean return from the callback, and two internal iterators
cannot be interleaved, because neither will yield control.

**Generator or coroutine backed.** The traversal is written as ordinary
straight-line or recursive code and the language suspends it at each yield. This
removes the hardest part of the external form, the hand-written state machine,
while keeping full external control for the consumer. Python generators, C#
iterator methods, JavaScript generator functions and Kotlin sequences are the
same idea in four languages. The compiler or runtime builds the state machine the
programmer would have written. The costs are a heap-allocated frame per live
generator, a suspension and resumption per element rather than a plain call, and
a resource-release path that runs only when the generator is closed or collected.
Python exposes that path as a close operation that raises a dedicated exception
at the suspension point so that cleanup code runs.

**Push iterators, the Go 1.23 form.** Go standardised the internal form as a
function type, so that the language loop can consume it. The iterator is a
function taking a yield callback that returns a boolean, and the loop stops when
yield returns false. The standard signatures are single value and key value pairs
([The Go Blog, range over function types](https://go.dev/blog/range-functions),
verified 2026-08-02). This is the internal form with a language-level early exit
protocol, which removes the usual internal-form drawback. Go also supplies a
conversion from push to pull, returning a next function and a stop function, for
the merge case where two sequences must advance independently. The pull side
costs a goroutine and requires the stop function to run, which is why the idiom
defers it immediately.

**Bulk and splitting traversal.** Java's splitting traversal object carries a
single-element advance, a bulk drain of the remainder, and an operation that
partitions the remaining elements into a second traversal object for parallel
work ([Java SE 21, `java.util.Spliterator`](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/Spliterator.html),
verified 2026-08-02). The bulk drain exists because the per-element two-call
protocol is a throughput cost, and the split exists because a plain cursor is a
serialisation point. This is the variant to reach for when the element work is
large and independent.

**Snapshot iterator.** The cursor copies the container's contents, or takes an
immutable persistent version of it, at creation. Mutation during traversal is
then impossible to observe and no detection machinery is needed. Costs are
memory proportional to the collection and a view that can be stale before the
loop ends. Persistent data structures make this variant close to free, which is
why it is the default in Clojure and in Scala's immutable collections.

**Weakly consistent iterator.** The cursor reads the live structure and gives no
guarantee about which concurrent changes it observes, while promising never to
fail and never to show a corrupt element. This is the concurrent-collection
answer and is covered as a production use in dimension 9.

**Fail-fast iterator.** The cursor records a modification count at creation and
compares it on each operation, throwing when it differs. This is the Java
Collections Framework answer for the non-concurrent collections. It is a bug
detector, not a safety mechanism, and dimension 11 explains why the difference
matters.

**Filtering and transforming adapters.** An iterator that wraps another iterator
and changes what it yields. This is Decorator applied to the cursor, and it is
what makes lazy pipelines possible, since each stage holds one element rather
than a whole intermediate collection. Rust's trait documentation states plainly
that iterators are lazy and that adapter methods do nothing until the iterator is
consumed ([Rust standard library, `std::iter::Iterator`](https://doc.rust-lang.org/std/iter/trait.Iterator.html),
verified 2026-08-02). The failure mode of this variant is a pipeline that is
built and never consumed, which is a silent no-op.

**Infinite or unbounded iterator.** The cursor never reports exhaustion. This is
only expressible in a lazy form and it is the reason laziness is more than an
optimisation. Python's iteration toolkit ships three of these, a counter, a
cycler and a repeater, and the documentation warns that streams of unbounded
length must only be reached by code that truncates them
([Python standard library, itertools](https://docs.python.org/3/library/itertools.html),
verified 2026-08-02). The interesting property is that an unbounded producer plus
a truncating consumer terminates, which lets a program describe a sequence
without deciding its length at the point of description.

**Null iterator.** An iterator over nothing, returned for a leaf node in a
composite structure, so that recursive traversal code needs no special case. This
is Null Object applied to the cursor and it removes a branch from every caller.

**Async iterator.** The advance operation returns a promise or a future rather
than a value, so that a suspension can wait on input or output. This is the shape
of the JavaScript async iteration protocol, of C# async streams, and of Python
async generators. The pattern is unchanged. what changes is that the consumer
loop is now a suspension point, so cancellation and resource release need an
answer for the abandoned-mid-loop case.

**Language note on Rust.** Rust has no inheritance, so the classical class
diagram does not translate. The Aggregate role is the trait that converts a value
into an iterator, the Iterator role is a trait with one associated element type
and one required advance operation returning an optional value, and the
ConcreteIterator is a plain struct holding the state. The borrow checker makes
the mutation-during-traversal failure a compile error rather than a runtime one,
which is the single largest practical difference between Rust and every other
language in this entry.

## 9. Known production uses

**Java Collections Framework, `java.util.Iterator` and the fail-fast contract.**
The interface carries four operations, a test for remaining elements, an advance,
an optional removal of the last returned element, and a bulk drain of the
remainder. Removal is documented as callable only once per advance, and advancing
past the end throws a dedicated exception rather than returning a sentinel
([Java SE 21, `java.util.Iterator`](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/Iterator.html),
verified 2026-08-02). The non-concurrent collections detect structural
modification during traversal and throw. The documentation for that exception is
unusually candid about what the mechanism is worth. it states that fail-fast
behaviour cannot be guaranteed in the presence of unsynchronised concurrent
modification, that the exception is thrown on a best-effort basis, and that
writing a program which depends on the exception for correctness would be wrong,
because the exception should be used only to detect bugs
([Java SE 21, `java.util.ConcurrentModificationException`](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/ConcurrentModificationException.html),
verified 2026-08-02).

**Java concurrent collections, weakly consistent iterators.** The concurrent hash
map takes the opposite design decision. Its documentation states that iterators,
splitting traversal objects and enumerations return elements reflecting the state
of the table at some point at or since the creation of the cursor, and that they
do not throw the concurrent modification exception
([Java SE 21, `java.util.concurrent.ConcurrentHashMap`](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/ConcurrentHashMap.html),
verified 2026-08-02). The same catalog therefore ships both answers to the
consistency force from dimension 3, with the choice pinned to the collection
rather than to the caller. This is the clearest real-world evidence that the
consistency question has no single correct answer.

**.NET enumerators and C# iterator methods.** The generic enumerator interface
carries an advance, a current element, a reset kept for interoperability, and a
disposal operation, and it inherits disposability so that a cursor can close a
database connection or release a file handle. The documentation states plainly
that enumerators cannot be used to change the underlying collection, and that if
the collection is changed by adding, modifying or deleting elements, the
behaviour of the enumerator is undefined. It also states that enumeration is not
thread safe and that callers must lock or supply their own synchronisation
([Microsoft .NET API documentation, `IEnumerator<T>`](https://learn.microsoft.com/en-us/dotnet/api/system.collections.generic.ienumerator-1),
verified 2026-08-02). The C# compiler then generates that enumerator from an
ordinary method containing yield statements, including the asynchronous form
built on the async enumerable interface and consumed with an awaiting loop
([Microsoft C# reference, the yield statement](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/statements/yield),
verified 2026-08-02).

**JavaScript iteration protocols, ECMA-262.** The language defines an iterable as
an object carrying a method under a well-known symbol that returns an iterator,
and an iterator as an object carrying an advance operation returning a record
with a completion flag and a value. Two optional operations complete the
contract, one signalling early termination so the producer can clean up, and one
injecting an error into the producer. Language features that stop early, such as
breaking out of a loop or an incomplete destructuring, call the termination
operation
([MDN, iteration protocols](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Iteration_protocols),
verified 2026-08-02; specified in [ECMA-262, control abstraction objects, operations on iterator objects](https://tc39.es/ecma262/multipage/control-abstraction-objects.html#sec-iteration),
verified 2026-08-02). Strings, arrays, typed arrays, maps, sets, the arguments
object and DOM node lists all implement it, which is what makes one loop form
work across unrelated container types.

**Node.js streams as async iterators.** A readable stream implements the
asynchronous iteration protocol, so a stream is consumed with an awaiting loop
rather than with event handlers. The documented behaviour on early exit is the
part worth knowing. if the loop is left by a break, a return or a throw, the
stream is destroyed
([Node.js documentation, `readable[Symbol.asyncIterator]()`](https://nodejs.org/api/stream.html#readablesymbolasynciterator),
verified 2026-08-02). This is the resource-lifetime force from dimension 3 given
a concrete and slightly surprising answer, and it is a behaviour that catches
teams who expected to resume the stream after peeking at one chunk.

**Rust standard library, the iterator trait.** The trait requires one associated
element type and one advance operation returning an optional value, with the
absent case meaning exhaustion, so there is no separate test for remaining
elements and no way to read a current element after the end. Everything else in
the trait is an adapter or a consumer built on that one operation, and the
documentation states that iterators are lazy and do no work until consumed
([Rust standard library, `std::iter::Iterator`](https://doc.rust-lang.org/std/iter/trait.Iterator.html),
verified 2026-08-02). The single-operation design removes an entire class of bug
that the two-operation shape allows, namely reading the current element in a
state where it is undefined.

**Go 1.23 range over function types.** Go added iterator support to the language
loop by defining function types in a standard package, one for single values and
one for pairs, both taking a yield callback whose boolean result signals whether
to continue. The standard slice and map packages gained operations returning
these iterators and operations collecting them back into containers
([The Go Blog, range over function types](https://go.dev/blog/range-functions),
verified 2026-08-02). This is the most recent large-scale adoption of the pattern
into a mainstream language's core, and it chose the push form rather than the
classical cursor.

**Python iteration protocol and the iteration toolkit.** The container protocol
requires an operation returning an iterator, the iterator protocol requires an
advance operation and an operation returning the iterator itself, which is what
allows both containers and cursors to be used by the loop statement
([Python standard types, iterator types](https://docs.python.org/3/library/stdtypes.html#iterator-types),
verified 2026-08-02). On top of that the standard library ships a set of
composable lazy building blocks described as fast and memory efficient, including
the three unbounded producers named in dimension 8
([Python standard library, itertools](https://docs.python.org/3/library/itertools.html),
verified 2026-08-02).

## 10. Consequences

Positive.

- The aggregate's storage is free to change, because no client names it. This is
  the payoff that motivated the pattern and it survives every variant.
- Several traversal orders can exist as separate named types over one container,
  each testable on its own, and a new order costs one class and no edits.
- Several traversals can run at once over one aggregate, since each cursor holds
  its own position, which the caller-held index approach cannot do safely.
- Traversal position becomes a value with a lifetime, so a walk can be paused,
  handed to another component, or resumed after a suspension.
- The loop in the client becomes uniform across container types, which is what
  lets generic algorithms be written once and reused everywhere.
- Lazy evaluation becomes expressible, which turns memory-bound problems into
  streaming ones and makes unbounded sequences describable.
- The cursor is a natural place to add cross-cutting behaviour, including
  filtering, batching, retry on a paged source, and instrumentation, because
  every element passes through one point.
- Early termination is cheap. A consumer that needs the first matching element
  causes only the work needed to produce that element.

Negative.

- Per-element interface dispatch costs more than an indexed loop over contiguous
  memory, and in the two-operation shape the cost is doubled.
- The concurrent modification question has to be answered explicitly per
  container, and every answer has a failure mode. Loud failure annoys callers,
  snapshots go stale and cost memory, weak consistency is hard to reason about.
- A hand-written cursor for a recursive structure is a state machine, which is
  much harder to read and to change than the recursive walk it replaces.
- Resource lifetime becomes tied to control flow, so an abandoned loop leaks
  unless the language and the implementation both handle the abandoned case.
- Work is hidden behind what looks like a local loop, which is how remote calls
  and disk reads end up inside code that reads like an array scan.
- One-pass semantics surprise readers who expect a collection. A cursor consumed
  twice yields nothing the second time, with no error in most languages.
- Debugging is harder. A stack trace taken inside a lazy pipeline shows the
  consumer and the adapter frames, not the code that described the pipeline.
- The pattern adds a type. For a small closed container it is pure overhead, see
  dimension 4.

## 11. Failure modes and misuse

**Structural modification during an external traversal.** Symptom. A
`ConcurrentModificationException` in Java, or an invalidated-iterator crash in
C++, or in Python a loop over a list that silently skips every second element
after a removal. The Java case usually appears with a stack trace pointing into
the collection's internal cursor class, with no application frame at the throw
site, and it often appears in a single-threaded method that removes inside a loop
over the same collection. Cause. The cursor's cached modification count no longer
matches the collection's, because the collection was changed through anything
other than the cursor's own removal operation. In Python there is no detection at
all for lists, so index-based skipping happens quietly, which is worse. Fix.
Remove through the cursor's own removal operation, or collect the elements to
remove and apply the change after the loop, or build a new collection. When the
mutation is genuinely concurrent, move to a container documented for concurrent
traversal. The most important correction is a mental one. the Java exception is
documented as a best-effort bug detector and not a guarantee, so code must not
catch it and retry as though it were a control mechanism.

**Treating fail-fast detection as thread safety.** Symptom. A production system
that reads a shared non-concurrent map from several threads runs for months, then
returns a corrupted value or spins in an infinite loop inside the map's internal
code, without any exception. Cause. Absence of the exception was read as evidence
that the traversal was safe. The exception is thrown on a best-effort basis and
unsynchronised modification can leave the structure in a state the cursor never
inspects. Fix. Use a concurrent container, or hold a lock across the whole
traversal, and treat any occurrence of the exception as a defect report rather
than as the safety net working.

**The leaked cursor over a scarce resource.** Symptom. Connection pool exhaustion
under load, or a steadily climbing count of open file descriptors, with the
process healthy in every other respect. The stack traces at exhaustion point at
unrelated code, because the leak is at the site that abandoned a loop, not at the
site that failed to get a connection. Cause. A lazy iterator backed by an open
database cursor or an open file was returned to a caller who exited the loop
early or never finished it, and the release path never ran. Fix. Tie the resource
to a scope the producer controls, materialise inside that scope when the result
set is bounded, or make the type disposable and require the caller to use the
language's scoped release construct. In JavaScript, implement the termination
operation of the iterator protocol so that a break in the consumer closes the
producer, which is what the Node.js stream implementation does by destroying the
stream on early exit.

**Consuming a one-pass iterator twice.** Symptom. A function that logs a count of
zero and then processes nothing, on data that is provably present, with no error
raised. Common in Python where a generator is passed to two consumers, and in
Java where a stream is reused. Cause. The cursor is in the exhausted state, and
the exhausted state is required to be sticky. Fix. Materialise once into a
collection when two passes are genuinely needed, or produce a fresh cursor per
pass by passing the container rather than the cursor. Add an assertion that fails
loudly when a spent cursor is reused, which several libraries do by throwing on a
second consumption.

**The lazy pipeline that never runs.** Symptom. A transformation with a side
effect, a log write, a metric increment, a database update, does not happen, and
the code that describes it is provably executed. Cause. A chain of adapters was
built and never consumed. Rust's documentation flags this directly, and the
compiler warns on an unused iterator for the same reason. Fix. End every pipeline
in a consuming operation, and move side effects out of the transformation stages,
where they do not belong regardless.

**The hidden N plus one.** Symptom. A page that renders in two hundred
milliseconds in development and in twelve seconds in production, with a database
showing thousands of near-identical small queries per request. Cause. An iterator
over parent rows whose element access lazily fetches child rows, so the loop that
reads like a local scan issues one query per element. Fix. Fetch the children in
one query and iterate the joined result, or batch the cursor so that it fetches a
window of children per advance. The general lesson is that a cursor hides where
elements come from, so any cursor crossing a process boundary should say so in
its name and its type.

**Unbounded consumption of an unbounded producer.** Symptom. A process consuming
memory until the runtime kills it, with a heap filled by one list, and no error
in the application logs. Cause. An endless producer was passed to an operation
that materialises, a collect, a sort, a length, or a container constructor. Fix.
Truncate before materialising. The Python documentation states the rule directly.
streams of unbounded length must only be reached by code that truncates them. In
review, treat a materialising operation applied to a value of unknown length as a
defect until the bound is shown.

**Hand-written cursor state that drifts from the container.** Symptom. A
traversal that returns the right elements for a container built one way and skips
or repeats elements for a container built another way, for example after a
resize, a rehash or a rebalance. Cause. The cursor duplicated an assumption about
the storage, usually a bucket index or a capacity, and one code path in the
container broke that assumption. Fix. Move the assumption behind an operation the
container owns, and add a property test that builds the container by random
operation sequences and asserts the traversal yields exactly the inserted
multiset.

**Iteration while holding a lock.** Symptom. Latency spikes and thread pool
starvation, with many threads blocked on one monitor whose holder is inside a
loop. Cause. The traversal was wrapped in a lock for safety, and the per-element
work inside the loop turned out to be slow or to perform input and output. Fix.
Copy under the lock and traverse outside it, or move to a container with
documented concurrent traversal so that no lock is needed for the read.

**Removal semantics misused.** Symptom. An `IllegalStateException` from a Java
collection cursor, or a silently skipped element, when a loop removes twice per
advance or removes before advancing. Cause. The removal operation is documented
as callable exactly once per advance, and the implementations enforce it only
partly. Fix. One removal per advance, and prefer the bulk conditional removal
operation on the collection when the goal is a filter, since it expresses the
intent without a cursor.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3. The
alternatives are real designs that appear in the same reviews, not strawmen.

| Force | External Iterator (GoF cursor) | Internal Iterator (forEach, Go push) | Return a materialised List or Slice | Expose an index and a size | Visitor | Observer or Reactive Streams | Splitting traversal (Spliterator) |
|---|---|---|---|---|---|---|---|
| Coupling to representation | Low. Client sees the cursor only | Low. Client sees the element only | Low, but commits to list semantics | High. Client encodes the storage | Low for structure, high for node types | Low. Client sees events | Low |
| Memory for a large sequence | One element plus position | One element plus a frame | Whole sequence resident | Whole sequence resident | Whole structure resident | One element in flight | One element per partition |
| Unbounded sequences | Expressible | Expressible with an early exit protocol | Impossible | Impossible | Impossible | Expressible, that is its home ground | Expressible with care |
| Early exit by the consumer | Direct. Stop calling advance | Needs a protocol, boolean return or exception | Free, break the loop | Free | Awkward, needs a flag in the visitor | Needs cancellation or backpressure | Direct on the sequential path |
| Interleaving two sequences | Direct. Two independent cursors | Not possible without a pull conversion | Direct | Direct | Not applicable | Possible with combinators | Possible per partition |
| Throughput per element | Two calls per element in the classical shape | One call per element, loop stays inside | Fastest. Plain indexed loop | Fastest | One dispatch per node | Highest overhead, scheduling per element | Bulk drain amortises the call |
| Parallelism | None. Serialisation point | None in the standard form | Easy, partition the list | Easy | Hard, order dependent | Depends on the scheduler | Strong. That is its purpose |
| Resource lifetime safety | Weak. Caller owns the loop | Strong. Producer wraps the loop | Strong. Resource closed before return | Strong | Strong | Explicit via subscription lifecycle | Strong on the bulk path |
| Behaviour under concurrent modification | Must be designed. Fail fast, snapshot, or weak | Same question, one loop to protect | Snapshot by construction | Undefined, caller's problem | Same question | Not applicable, source drives | Fail fast or late binding |
| Cognitive load to implement | High for recursive structures | Low. Write the natural loop | Lowest | Lowest | High. Two hierarchies | High. Backpressure is subtle | High |
| Cognitive load to consume | Low with language loop syntax | Low, but early exit reads oddly | Lowest | Low | High | High | Low, usually via a stream API |
| Adding a new traversal order | New cursor class, no edits | New method or function | New method returning a new list | New index scheme, edits callers | New traversal in the structure | New operator | New splitting object |
| Adding a new operation over elements | Free, write a new consumer | Free | Free | Free | Free, that is Visitor's purpose | Free | Free |
| Operability | Poor. Source of elements is hidden | Poor for the same reason | Good. Cost paid before return, visible | Good | Medium | Medium, with subscription metrics | Medium |

Reading of the table. The external form wins when the consumer needs control,
which covers early exit, interleaving and suspension. The internal and push forms
win on resource safety and on the difficulty of writing the producer, which is
why Go chose push and why most functional APIs are internal. A materialised list
wins whenever the sequence is small and bounded and the caller wants random
access, and it is the honest choice far more often than pattern enthusiasm
suggests. Visitor wins when the shape of the structure, rather than the sequence
of elements, is the thing the algorithm needs. Reactive streams win when the
source, not the consumer, decides when data appears. The splitting form wins when
per-element work is large and independent.

## 13. Related and incompatible patterns

- **Factory Method.** Composes directly, and the composition is in the GoF
  structure itself. The aggregate's operation that produces a cursor is a factory
  method, which is what allows a container interface to promise a traversal
  without naming a cursor type. Java's collection interface declaring a cursor
  operation is the canonical instance of both patterns at once.
- **Composite.** The pattern that most often needs a hand-written cursor. A
  composite structure has no linear storage, so the cursor holds an explicit
  stack or queue and the choice of stack or queue is the choice of depth-first
  or breadth-first. This is the case where a generator earns its keep most
  clearly, because the recursive walk can be written as recursion.
- **Null Object.** Applied to the cursor. A leaf in a composite returns an empty
  iterator rather than a null reference, so the recursive traversal has no
  special case for leaves.
- **Visitor.** A substitute, not a partner, when the structure matters. Iterator
  linearises a structure and hands elements over one at a time. Visitor preserves
  the structure and dispatches on node type. Choose Iterator when consumers care
  about the elements, Visitor when they care about the shape. Combining them, by
  iterating a composite and dispatching on type inside the loop, produces the
  type switch that Visitor exists to remove.
- **Decorator.** How lazy pipelines are built. A filtering or mapping cursor
  wraps another cursor and satisfies the same interface, so stages compose with
  no knowledge of each other and no intermediate collection.
- **Memento.** The GoF pairing for a cursor that must tolerate modification. The
  cursor asks the aggregate for an opaque token capturing enough state to resume
  correctly after a change, which keeps the cursor from encoding the storage.
  Rarely built by hand today, because snapshot and weakly consistent containers
  cover the same need at lower cost.
- **Template Method.** The internal form is usually a template method. The
  aggregate owns the sequencing of the loop and the client supplies the
  per-element operation as the hook.
- **Strategy.** Frequently confused with the traversal-order variant. Selecting a
  depth-first or breadth-first cursor at runtime is Strategy over cursor
  construction. The distinction is that Strategy substitutes a policy while
  Iterator holds a position, and a cursor that has no position is not this
  pattern.
- **Observer and Reactive Streams.** The inverted twin. Iterator is pull, Observer
  is push without backpressure, and reactive streams are push with a demand
  signal that restores the consumer's control. They do not compose in one
  direction. blocking inside a cursor's advance operation to wait for a pushed
  event turns an asynchronous source into a parked thread, which is the standard
  way this conflict shows up in production.
- **Repository.** Composes, with a caution. Returning a lazy cursor from a
  repository leaks the storage session's lifetime into application code, which
  is the leaked-cursor failure in dimension 11. Return a materialised result, or
  return a type whose name says the caller now owns a resource.
- **Iterator over an aggregate that is also a Proxy.** Actively conflicts unless
  designed for. A lazy loading proxy behind each element turns the loop into the
  hidden N plus one from dimension 11.

## 14. Refactoring path in and out

Introducing the pattern into code that does not have it. The applicable named
refactorings are Encapsulate Collection and Replace Loop with Pipeline, see the
refactoring family entries.

1. Find the callers that reach into the container's storage. Grep for the field,
   for the accessor that returns the internal list, and for index arithmetic on
   the container's size. This set is the blast radius and it must be known before
   anything moves.
2. Catalogue the traversal orders those callers actually use. Most codebases have
   fewer than they appear to, and two callers with slightly different orders
   usually reveal a bug in one of them.
3. Add the traversal operation to the container, returning the language's
   standard iterable type over the element type. Implement it by delegating to
   the storage's own cursor. Nothing else changes. Run the tests.
4. Move one caller at a time to the new operation, keeping the old accessor in
   place. Run the tests after each caller. Resist changing behaviour during this
   step, since a traversal change and a logic change in one commit cannot be
   bisected apart.
5. When every caller has moved, remove the accessor that exposed the storage.
   This is the commit that actually buys the decoupling. Steps 3 and 4 buy
   nothing on their own, which is why partial migrations are common and worth
   nothing.
6. Only now add a second traversal order, if one is needed, as a second named
   operation. Adding it earlier makes step 4 harder for no gain.
7. Decide the concurrent modification policy and write it into the container's
   documentation. Fail fast, snapshot, or weakly consistent. An undocumented
   policy is a policy of undefined behaviour, which callers will discover in
   production.
8. If the traversal is recursive, write it as a generator rather than as a
   hand-rolled state machine, unless the language lacks generators or the
   allocation per traversal is measured and unacceptable.

Removing the pattern when it stops earning its place. The signals are a cursor
type with one implementation and one caller, a container whose storage has been
the same for years and is public anyway, or a lazy cursor whose every consumer
immediately materialises it.

1. Confirm the laziness is unused. Check every consumer for a materialising
   operation as the first thing it does. If they all materialise, the laziness is
   costing dispatch and buying nothing.
2. Confirm no consumer relies on early exit or on interleaving. Those two are the
   properties that only a cursor gives, and removing the cursor removes them.
3. Change the traversal operation to return a materialised collection, keeping
   the same name and element type where the language allows it. Run the tests.
4. Delete the cursor class. If it held a resource, move the resource scope into
   the operation that now materialises, which is a net improvement in resource
   safety.
5. If the container is small and internal and now has one caller, inline it. This
   is Inline Class, see the refactoring family entry.
6. Keep the traversal operation even when the cursor is gone. The decoupling from
   storage was the point, and returning a copy still delivers it.

## 15. Testing and verification

Easier because of the pattern.

- A consumer can be tested against a hand-written cursor with no container at
  all, which removes container setup from consumer tests entirely.
- Empty, one-element and many-element cases become trivial to construct as test
  inputs, so boundary coverage is cheap.
- Laziness is directly assertable. Build a producer that increments a counter per
  element, apply the transformation chain, assert the counter is zero, consume a
  prefix, assert the counter equals the prefix length. This test catches an
  accidental materialisation in a pipeline stage, which is a common performance
  regression that no other test finds.
- Error behaviour can be injected precisely. A cursor that yields two elements
  and then throws is three lines and exercises the consumer's partial-failure
  path, which is otherwise hard to reach.

Harder because of the pattern.

- What the loop actually did is invisible from the outside. Assertions have to be
  on the consumed elements or on a counter, since no source line names the
  traversal order.
- Concurrent modification behaviour is nondeterministic by design in the fail-fast
  form, because the detection is documented as best effort, so a test that
  asserts the exception is thrown can be flaky under a different implementation
  or a different collection.
- Resource release on the abandoned-loop path is easy to forget to test, and it
  is the path that leaks in production.

Techniques that apply.

- **Contract test over the iterator protocol.** One abstract test suite with a
  hook that supplies a cursor, subclassed once per implementation. Assert the
  sticky exhausted state, assert that reading the current element after
  exhaustion is an error or undefined per the language contract, assert that the
  removal operation is rejected before the first advance, and assert that the
  yielded multiset equals the container's contents. This is the single highest
  value test for any hand-written cursor.
- **Property test on traversal completeness.** Generate random operation
  sequences against the container, then assert that the traversal yields exactly
  the multiset of surviving elements and, where the container promises an order,
  that the order matches an independently computed reference. This finds the
  drifted-cursor-state failure from dimension 11, which example tests miss
  because the failing case only appears after a resize or a rebalance.
- **Abandoned-loop resource test.** Consume one element, break, then assert the
  resource is released. Assert the same for an exception thrown from inside the
  loop body. In JavaScript this is a test that the termination operation ran, in
  .NET that disposal ran, in Python that the generator's close path ran.
- **Fake cursor over a fake source for the paged case.** A cursor over a remote
  paged API should be tested against a fake that counts page requests, so the
  test asserts the page count as well as the element sequence. Page count is the
  property that regresses when someone changes the buffering, and no
  element-level assertion notices.
- **Two-pass test.** Assert explicitly that a second consumption yields nothing,
  or throws, whichever the type promises. This pins one-pass semantics so a later
  change to a re-iterable implementation is a deliberate decision rather than an
  accident.
- **Reference implementation differential.** For an order that is not obvious,
  such as an in-order tree walk, keep a slow recursive reference implementation
  in the test code and assert the fast cursor agrees with it on random
  structures.

## 16. Observability signals

The pattern hides where elements come from and how much work each one costs, so
the traversal has to appear in telemetry or an operator has nothing to work with.

What to record.

- A counter of elements yielded, labelled by the traversal's name and by the
  source. This is the most useful single signal, because it turns an invisible
  loop into a rate that can be compared against the expected volume.
- A histogram of the time from cursor creation to first element, kept separately
  from the total traversal duration. Those two numbers answer different
  questions. The first exposes eager work hiding in a supposedly lazy producer,
  the second exposes a slow per-element path.
- A counter of traversals started and a counter of traversals completed, as
  separate series. The gap between them is the abandoned-loop rate, which is
  exactly the population that leaks resources.
- For any cursor holding a resource, a gauge of live cursors and a histogram of
  cursor lifetime. A gauge that only climbs is the leak from dimension 11, seen
  before the connection pool fails rather than after.
- For a cursor over a paged remote source, a counter of page requests and a
  histogram of elements per page. Elements per page falling is a source-side
  change that multiplies request count with no code change on this side.
- A counter of concurrent modification detections, labelled by container and by
  call site. This should sit at zero. Any nonzero value is a defect report,
  because the exception is documented as a bug detector rather than as a control
  mechanism.
- For a batching cursor, a counter of refills and the batch size distribution.

A healthy instance on a dashboard. Traversals started and completed track each
other closely, with the small difference explained by known early-exit paths such
as a search that stops on the first match. Time to first element is small and
flat, and much smaller than total traversal duration. The live cursor gauge is
flat and returns to zero between load periods. Page requests per traversal match
the expected element count divided by the expected page size. The concurrent
modification counter is zero.

A failing instance. Traversals started climbs while completed stays flat, which
means consumers are abandoning loops, and the live cursor gauge will confirm it
by climbing in step. Or time to first element rises to match total duration,
which means the producer became eager, usually after a change to one pipeline
stage. Or page requests per traversal jump while element counts are unchanged,
which means the page size collapsed upstream. Or elements yielded goes to zero
while traversals started continues, which is the spent-cursor reuse from
dimension 11 and produces no errors at all, so this counter is the only way to
see it. Or the concurrent modification counter leaves zero, which localises a
defect to a container and a call site without reading any code.

## 17. Security and privacy implications

The pattern is close to silent on security in the local, in-memory case where the
container and the consumer are in one process and the elements are already
authorised. Claiming otherwise would be inventing a concern. Four genuine
implications appear once the cursor crosses a trust boundary or a process
boundary.

**Unbounded iteration as a denial of service.** A cursor makes it natural to
write a loop whose length is controlled by the data rather than by the code. When
the data is attacker-influenced, a request that looks constant-cost becomes
linear or worse in an input the attacker chooses. The pattern makes this easy to
write and hard to see, because the loop body reads the same whether the sequence
has ten elements or ten million. Bound the number of elements consumed per
request, apply a deadline to the loop rather than to each element, and treat any
materialising operation over a value of unknown length as a defect until the
bound is shown, which is the same rule the Python documentation states for
unbounded producers.

**Pagination tokens as a leaked capability.** A cursor over a remote source is
usually implemented with a continuation token that the client sends back. When
that token encodes a query, an offset, or a filter, it is a capability. If it is
not bound to the caller's identity and not integrity protected, a client can
alter it and read a neighbouring tenant's page, which is an insecure direct
object reference wearing a pagination token's clothes. Bind the token to the
authenticated subject, sign or encrypt it, give it an expiry, and re-check
authorisation on every page rather than only on the first request. The re-check
matters because entitlements can be revoked between page one and page nine, and a
long-lived cursor is exactly the case where that gap is wide.

**Snapshot cursors serving revoked or deleted data.** A snapshot iterator by
design shows the state at creation time. If an element is deleted for a legal
reason, a takedown, a retention expiry, or a data subject's erasure request,
every open snapshot cursor keeps serving it until the traversal ends. Weakly
consistent cursors have a milder version of the same property, since they promise
only that elements reflect the state at some point at or since creation. Where
deletion has a compliance meaning, either re-check each element against a
current authoritative source before returning it, or bound cursor lifetime so
that the exposure window is short and stated.

**Resource exhaustion through cursor accumulation.** Each open cursor over a
remote or file-backed source holds server-side state. An endpoint that creates a
cursor per request and depends on the client finishing the loop to release it can
be exhausted by a client that opens many cursors and abandons all of them, with
no invalid request ever sent. Cap concurrent cursors per subject, expire idle
cursors on a timer independent of the client, and treat the abandoned-loop
counter from dimension 16 as a security signal and not only as a hygiene one.

On privacy the pattern is neutral in itself, with two practical caveats. First,
the observability advice in dimension 16 says to count elements by source and by
traversal name. Element counts can be attributable. the number of records in one
tenant's traversal is a fact about that tenant, and a per-tenant label turns a
counter into a small data disclosure to anyone with dashboard access. Aggregate
or bucket where that matters. Second, a cursor that batches for efficiency holds
a window of elements in memory for longer than a one-element cursor does, which
widens the window in which personal data appears in a heap dump or a crash
report. Where the elements carry personal data, prefer the smallest batch that
meets the throughput target rather than the largest one that fits.

## 18. References

1. Erich Gamma, Richard Helm, Ralph Johnson, John Vlissides. *Design Patterns.
   Elements of Reusable Object-Oriented Software*. Addison-Wesley, 1994.
   ISBN 0-201-63361-2. Chapter 5, Behavioral Patterns, section Iterator, pages
   257 to 271. Source of the intent, the Cursor alias, the five participants, the
   external and internal control distinction in the Implementation section, and
   the Memento pairing for a modification-tolerant cursor.
2. Barbara Liskov, Alan Snyder, Russell Atkinson, Craig Schaffert. "Abstraction
   Mechanisms in CLU". *Communications of the ACM*, volume 20, number 8, 1977,
   pages 564 to 576. https://dl.acm.org/doi/10.1145/359763.359789
   Verified 2026-08-02. Source for the pre-GoF lineage of iterators as a
   first-class control abstraction.
3. Oracle. *Java SE 21 API Specification*, `java.util.Iterator`.
   https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/Iterator.html
   Verified 2026-08-02. Source for the four operations and the once-per-advance
   removal rule.
4. Oracle. *Java SE 21 API Specification*,
   `java.util.ConcurrentModificationException`.
   https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/ConcurrentModificationException.html
   Verified 2026-08-02. Source for the fail-fast definition, the best-effort
   caveat, and the statement that the exception should be used only to detect
   bugs.
5. Oracle. *Java SE 21 API Specification*,
   `java.util.concurrent.ConcurrentHashMap`.
   https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/ConcurrentHashMap.html
   Verified 2026-08-02. Source for weakly consistent traversal and for the
   statement that its cursors do not throw the concurrent modification exception.
6. Oracle. *Java SE 21 API Specification*, `java.util.Spliterator`.
   https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/Spliterator.html
   Verified 2026-08-02. Source for the bulk and splitting traversal variant and
   for late binding.
7. Oracle. *Java SE 21 API Specification*, `java.lang.Iterable`.
   https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/Iterable.html
   Verified 2026-08-02. Source for the internal iterator form and for the
   enhanced loop statement.
8. Python Software Foundation. *The Python Standard Library*, Built-in Types,
   Iterator Types.
   https://docs.python.org/3/library/stdtypes.html#iterator-types
   Verified 2026-08-02. Source for the protocol operations and for the sticky
   exhausted state requirement.
9. Python Software Foundation. *The Python Language Reference*, Expressions,
   Yield expressions.
   https://docs.python.org/3/reference/expressions.html#yield-expressions
   Verified 2026-08-02. Source for generator semantics, suspension and resumption,
   and the close path used for cleanup.
10. Python Software Foundation. *The Python Standard Library*, itertools.
    https://docs.python.org/3/library/itertools.html
    Verified 2026-08-02. Source for the unbounded producers and for the rule that
    unbounded streams must only be reached by truncating code.
11. Microsoft. *.NET API documentation*, `System.Collections.Generic.IEnumerator<T>`.
    https://learn.microsoft.com/en-us/dotnet/api/system.collections.generic.ienumerator-1
    Verified 2026-08-02. Source for the .NET enumerator contract, the undefined
    current element before the first advance and after the end, the undefined
    behaviour under modification, and the thread-safety statement.
12. Microsoft. *C# language reference*, The yield statement.
    https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/statements/yield
    Verified 2026-08-02. Source for compiler-generated iterators, deferred
    execution, and the asynchronous iterator form.
13. Mozilla. *MDN Web Docs*, Iteration protocols.
    https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Iteration_protocols
    Verified 2026-08-02. Source for the iterable and iterator protocols, the
    result record, and the optional termination and error operations.
14. Ecma International. *ECMAScript Language Specification*, Control Abstraction
    Objects, Operations on Iterator Objects.
    https://tc39.es/ecma262/multipage/control-abstraction-objects.html#sec-iteration
    Verified 2026-08-02. Normative source for the JavaScript iteration protocol.
15. OpenJS Foundation. *Node.js documentation*, Stream,
    `readable[Symbol.asyncIterator]()`.
    https://nodejs.org/api/stream.html#readablesymbolasynciterator
    Verified 2026-08-02. Source for streams as async iterators and for stream
    destruction on early loop exit.
16. Rust project. *Rust standard library documentation*, `std::iter::Iterator`.
    https://doc.rust-lang.org/std/iter/trait.Iterator.html
    Verified 2026-08-02. Source for the single-operation trait, the associated
    element type, laziness, and adapters.
17. The Go project. "Range Over Function Types". *The Go Blog*.
    https://go.dev/blog/range-functions
    Verified 2026-08-02. Source for the Go 1.23 push iterator signatures, the
    yield early exit protocol, and the push to pull conversion.
18. Wikipedia contributors. "Iterator pattern".
    https://en.wikipedia.org/wiki/Iterator_pattern
    Verified 2026-08-02. Used only to confirm the wording of the GoF intent and
    the page range attribution, not as a source of explanation.

## Code examples

Five languages, chosen because each shows a different real shape of the pattern
rather than the same shape restated. Python shows the external cursor, the
generator that replaces it, and the internal form. TypeScript shows the language
protocol plus an unbounded lazy sequence. Go shows the push form added in 1.23
and the pull conversion. Rust shows the single-operation trait. Java shows the
fail-fast failure and its two correct fixes, because that failure is the one
readers actually hit.

C++ is omitted despite being the pattern's spiritual home, because its iterator
categories and the invalidation rules per container are a chapter rather than a
snippet, and a short example would misrepresent them.

The Python and Go examples below were run on the authoring machine and produced
the output described. The TypeScript examples were run as JavaScript with the
type annotations removed, because no TypeScript compiler is installed there, so
the runtime behaviour is confirmed and the type checking is not. The Java example
was written against the documented behaviour of the collection classes but not
executed, because no Java runtime is installed there. The Rust example was
written against the trait's documented contract but not compiled, for the same
reason.

### Python

External cursor written out by hand, which is the classical form and also the
form nobody should write for a list.

```python
class Ring:
    def __init__(self, items: list[str]) -> None:
        self._items = items

    def __iter__(self) -> "RingCursor":
        return RingCursor(self._items)


class RingCursor:
    def __init__(self, items: list[str]) -> None:
        self._items = items
        self._pos = 0

    def __iter__(self) -> "RingCursor":
        return self

    def __next__(self) -> str:
        if self._pos >= len(self._items):
            raise StopIteration
        value = self._items[self._pos]
        self._pos += 1
        return value


print(list(Ring(["a", "b", "c"])))
```

The same traversal as a generator. The state machine is gone and the code reads
as the walk it describes. For a tree this difference is the whole argument.

```python
class Node:
    def __init__(self, value, left=None, right=None):
        self.value = value
        self.left = left
        self.right = right

    def in_order(self):
        if self.left:
            yield from self.left.in_order()
        yield self.value
        if self.right:
            yield from self.right.in_order()


tree = Node(2, Node(1), Node(3))
print(list(tree.in_order()))
```

Laziness and an unbounded sequence, plus the truncation that makes it terminate.

```python
from itertools import count, islice


def squares():
    for n in count(1):
        yield n * n


print(list(islice(squares(), 5)))
```

The internal form, where the container drives and the caller supplies the
operation. The boolean return is the early exit protocol that the external form
gets for free.

```python
class Ledger:
    def __init__(self, rows):
        self._rows = rows

    def each(self, action) -> None:
        for row in self._rows:
            if action(row) is False:
                return


Ledger([1, 2, 3, 4]).each(lambda r: r < 2)
```

### TypeScript

The language protocol. Implementing the well-known symbol makes the type work
with the loop syntax, with spreading and with destructuring, at no further cost.

```typescript
class Ring implements Iterable<string> {
  constructor(private readonly items: string[]) {}

  [Symbol.iterator](): Iterator<string> {
    let pos = 0;
    const items = this.items;
    return {
      next(): IteratorResult<string> {
        return pos < items.length
          ? { value: items[pos++], done: false }
          : { value: undefined, done: true };
      },
      return(): IteratorResult<string> {
        pos = items.length;
        return { value: undefined, done: true };
      },
    };
  }
}

console.log([...new Ring(["a", "b", "c"])]);
```

An unbounded generator and a truncating adapter. The adapter is Decorator applied
to the cursor, and nothing runs until the loop pulls.

```typescript
function* naturals(): Generator<number> {
  for (let n = 1; ; n++) yield n;
}

function* take<T>(src: Iterable<T>, n: number): Generator<T> {
  let i = 0;
  for (const v of src) {
    if (i++ >= n) return;
    yield v;
  }
}

console.log([...take(naturals(), 5)]);
```

### Go

The push form standardised in Go 1.23. The iterator is a function receiving a
yield callback, and returning false from yield stops the producer.

```go
package main

import (
	"fmt"
	"iter"
)

type Ring struct{ items []string }

func (r Ring) All() iter.Seq[string] {
	return func(yield func(string) bool) {
		for _, v := range r.items {
			if !yield(v) {
				return
			}
		}
	}
}

func Take[V any](s iter.Seq[V], n int) iter.Seq[V] {
	return func(yield func(V) bool) {
		i := 0
		for v := range s {
			if i >= n || !yield(v) {
				return
			}
			i++
		}
	}
}

func main() {
	r := Ring{items: []string{"a", "b", "c", "d"}}
	for v := range Take(r.All(), 2) {
		fmt.Println(v)
	}
}
```

The pull conversion, which is how two sequences are advanced independently. The
stop function is deferred immediately, because failing to call it leaks the
goroutine that drives the push side.

```go
package main

import (
	"fmt"
	"iter"
	"slices"
)

func Equal[E comparable](a, b iter.Seq[E]) bool {
	nextA, stopA := iter.Pull(a)
	defer stopA()
	nextB, stopB := iter.Pull(b)
	defer stopB()
	for {
		x, okA := nextA()
		y, okB := nextB()
		if okA != okB {
			return false
		}
		if !okA {
			return true
		}
		if x != y {
			return false
		}
	}
}

func main() {
	fmt.Println(Equal(slices.Values([]int{1, 2}), slices.Values([]int{1, 2})))
	fmt.Println(Equal(slices.Values([]int{1, 2}), slices.Values([]int{1, 3})))
}
```

### Rust

One associated element type and one advance operation. There is no separate test
for remaining elements, so the state where the current element is undefined
cannot be reached.

```rust
struct Fib {
    a: u64,
    b: u64,
}

impl Iterator for Fib {
    type Item = u64;

    fn next(&mut self) -> Option<u64> {
        let out = self.a;
        self.a = self.b;
        self.b = out + self.b;
        Some(out)
    }
}

fn main() {
    let f = Fib { a: 0, b: 1 };
    let first: Vec<u64> = f.take(8).collect();
    println!("{:?}", first);
}
```

### Java

The failure from dimension 11, and the two correct fixes. The first fix uses the
cursor's own removal operation. The second expresses the intent as a filter and
avoids the cursor entirely.

```java
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;

public final class Removal {
    public static void main(String[] args) {
        List<String> a = new ArrayList<>(List.of("keep", "drop", "keep"));
        try {
            for (String s : a) {
                if (s.equals("drop")) {
                    a.remove(s);
                }
            }
        } catch (java.util.ConcurrentModificationException e) {
            System.out.println("detected: " + e.getClass().getSimpleName());
        }

        List<String> b = new ArrayList<>(List.of("keep", "drop", "keep"));
        Iterator<String> it = b.iterator();
        while (it.hasNext()) {
            if (it.next().equals("drop")) {
                it.remove();
            }
        }
        System.out.println(b);

        List<String> c = new ArrayList<>(List.of("keep", "drop", "keep"));
        c.removeIf(s -> s.equals("drop"));
        System.out.println(c);
    }
}
```
